from __future__ import annotations

import base64
import html
import json
import re
import shutil
import subprocess
import time
from pathlib import Path


CREATE_NO_WINDOW = 0x08000000


def _powershell_executable() -> str:
    for name in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        path = shutil.which(name)
        if path:
            return path
    candidates = (
        Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"),
        Path("C:/Program Files/PowerShell/7/pwsh.exe"),
    )
    for path in candidates:
        if path.exists():
            return str(path)
    raise FileNotFoundError("未找到 PowerShell，请确认 Windows PowerShell 或 PowerShell 7 已安装。")


def _run_powershell(script: str) -> subprocess.CompletedProcess:
    utf8_preamble = """
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Console]::OutputEncoding
    $ProgressPreference = 'SilentlyContinue'
    $VerbosePreference = 'SilentlyContinue'
    $WarningPreference = 'Continue'
    """
    encoded = base64.b64encode((utf8_preamble + "\n" + script).encode("utf-16le")).decode("ascii")
    try:
        return subprocess.run(
            [_powershell_executable(), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
            timeout=25,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("检测蓝牙设备超时，请稍后重试，或确认蓝牙驱动/设备管理器响应正常。") from exc


def _clean_powershell_detail(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if text.startswith("#< CLIXML") or "<Objs" in text:
        errors = re.findall(r'<S S="Error">(.*?)</S>', text, flags=re.DOTALL)
        if errors:
            text = "\n".join(html.unescape(item) for item in errors)
        else:
            text = re.sub(r"#< CLIXML.*", "", text, flags=re.DOTALL).strip()
    text = text.replace("_x000D__x000A_", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _run_pnputil(instance_id: str, enable: bool) -> tuple[bool, str]:
    action = "/enable-device" if enable else "/disable-device"
    command = ["pnputil", action, instance_id]
    if not enable:
        command.append("/force")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
        timeout=20,
    )
    detail = (result.stderr or result.stdout or "").strip()
    return result.returncode == 0, detail


def _radio_script(operation: str, enable: bool | None = None) -> str:
    state_line = ""
    if operation == "set":
        state = "On" if enable else "Off"
        state_line = f"""
        $targetState = [Windows.Devices.Radios.RadioState]::{state}
        $setResult = Await ($bluetooth.SetStateAsync($targetState)) ([Windows.Devices.Radios.RadioAccessStatus])
        "SetResult=$setResult"
        """
    return f"""
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    [Windows.Devices.Radios.RadioAccessStatus, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    [Windows.Devices.Radios.RadioKind, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    [Windows.Devices.Radios.RadioState, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null

    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object {{
            $_.Name -eq 'AsTask' -and
            $_.IsGenericMethod -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        }} | Select-Object -First 1)

    function Await($asyncOperation, [Type]$resultType) {{
        $asTask = $asTaskGeneric.MakeGenericMethod($resultType)
        $task = $asTask.Invoke($null, @($asyncOperation))
        $task.Wait() | Out-Null
        return $task.Result
    }}

    $access = Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
    if ($access -ne [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {{
        "Access=$access"
        exit 3
    }}

    $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
    $bluetooth = $radios | Where-Object {{ $_.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth }} | Select-Object -First 1
    if ($null -eq $bluetooth) {{
        "NoBluetoothRadio"
        exit 4
    }}

    "StateBefore=$($bluetooth.State)"
    {state_line}
    "StateAfter=$($bluetooth.State)"
    """


def _set_bluetooth_radio(enable: bool) -> tuple[bool, str]:
    result = _run_powershell(_radio_script("set", enable))
    detail = _clean_powershell_detail(result.stderr or result.stdout or "")
    return result.returncode == 0 and "SetResult=Allowed" in detail, detail


def _get_bluetooth_radio_status() -> bool | None:
    try:
        result = _run_powershell(_radio_script("get"))
    except Exception:
        return None
    detail = _clean_powershell_detail(result.stderr or result.stdout or "")
    if result.returncode != 0:
        return None
    if "StateBefore=On" in detail:
        return True
    if "StateBefore=Off" in detail:
        return False
    return None


def discover_bluetooth_adapters() -> list[dict]:
    script = """
    $devices = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $_.Class -eq 'Bluetooth' }
    $items = foreach ($d in $devices) {
        $name = [string]$d.FriendlyName
        $id = [string]$d.InstanceId
        $isAdapter = $false
        if ($id -match '^(USB|PCI|ACPI)\\') { $isAdapter = $true }
        if ($name -match '(?i)(adapter|radio|wireless bluetooth|bluetooth usb|bluetooth device)$') { $isAdapter = $true }
        if ($id -match '^(BTHENUM|BTHLE)\\') { $isAdapter = $false }
        if ($name -match '(?i)(airpods|headphones|headset|phone|audio|avrcp|nap|rfcomm|enumerator)') { $isAdapter = $false }

        [PSCustomObject]@{
            InstanceId = $d.InstanceId
            FriendlyName = $d.FriendlyName
            Status = $d.Status
            Service = ''
            Enumerator = ''
            IsAdapter = $isAdapter
        }
    }

    $recommended = @($items | Where-Object { $_.IsAdapter })
    if ($recommended.Count -gt 0) {
        $recommended | ConvertTo-Json -Depth 3
    } else {
        $items | ConvertTo-Json -Depth 3
    }
    """
    result = _run_powershell(script)
    if not result.stdout.strip():
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    adapters = []
    for item in data:
        instance_id = item.get("InstanceId")
        if not instance_id:
            continue
        is_adapter = bool(item.get("IsAdapter"))
        name = item.get("FriendlyName") or instance_id
        if not is_adapter:
            name = f"可能不是适配器：{name}"
        adapters.append(
            {
                "instance_id": instance_id,
                "name": name,
                "status": item.get("Status") or "Unknown",
                "service": item.get("Service") or "",
                "enumerator": item.get("Enumerator") or "",
                "is_adapter": is_adapter,
            }
        )
    return adapters


def set_bluetooth(instance_id: str, enable: bool) -> tuple[bool, str]:
    radio_ok, radio_detail = _set_bluetooth_radio(enable)
    if radio_ok:
        return True, radio_detail or "Windows 蓝牙开关操作成功"

    escaped = instance_id.replace('"', '\\"')
    action = "Enable-PnpDevice" if enable else "Disable-PnpDevice"
    script = f'{action} -InstanceId "{escaped}" -Confirm:$false'
    result = _run_powershell(script)
    if result.returncode == 0:
        return True, _clean_powershell_detail(result.stderr or result.stdout or "")

    ps_detail = _clean_powershell_detail(result.stderr or result.stdout or "")
    pnputil_ok, pnputil_detail = _run_pnputil(instance_id, enable)
    if pnputil_ok:
        return True, pnputil_detail or "pnputil 操作成功"

    detail = "\n".join(item for item in (ps_detail, pnputil_detail, radio_detail) if item)
    return False, detail or "PowerShell 和 pnputil 均未能完成操作"


def get_bluetooth_status(instance_id: str) -> bool:
    radio_status = _get_bluetooth_radio_status()
    if radio_status is not None:
        return radio_status

    escaped = instance_id.replace('"', '\\"')
    script = f"""
    $d = Get-PnpDevice -InstanceId "{escaped}" -ErrorAction SilentlyContinue
    if ($d) {{ $d.Status -eq 'OK' }} else {{ $false }}
    """
    result = _run_powershell(script)
    return "True" in result.stdout


def set_bluetooth_verified(instance_id: str, enable: bool, retries: int | None = None, delay: float | None = None) -> tuple[bool, str]:
    retries = retries if retries is not None else (12 if enable else 5)
    delay = delay if delay is not None else (1.2 if enable else 0.8)
    command_ok, detail = set_bluetooth(instance_id, enable)
    for _ in range(retries):
        time.sleep(delay)
        if get_bluetooth_status(instance_id) == enable:
            return True, "操作成功"
    if not command_ok and detail:
        return False, detail
    return False, f"验证超时：蓝牙未变为{'开启' if enable else '关闭'}状态"
