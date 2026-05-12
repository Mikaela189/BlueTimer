# BlueTimer

BlueTimer 是一个 Windows 蓝牙定时开关工具。程序常驻系统托盘，可以按规则自动开启或关闭蓝牙，适合“上班关闭蓝牙、下班开启蓝牙”这类固定时间场景。

## 当前版本

- 版本：`0.1.x`
- 目标系统：Windows 10 / Windows 11 x64
- 发布形式：单文件安装包 / 单文件主程序
- 权限要求：管理员权限

最新安装包：

```text
D:\啊\bluetimer\release\BlueTimer_Setup_v0.1.3.exe
```

最新主程序：

```text
D:\啊\bluetimer\dist\BlueTimer.exe
```

## 安装和使用

推荐直接运行安装包：

```text
BlueTimer_Setup_v0.1.3.exe
```

安装后会创建桌面快捷方式和开始菜单快捷方式。首次启动时，程序会检测蓝牙适配器；如果只检测到一个明确适配器，会自动选择，否则会弹出列表让用户选择。

设置定时规则示例：

- 上班关闭蓝牙：动作选择“关闭蓝牙”，时间设为 `09:00`，重复选择周一至周五。
- 下班开启蓝牙：动作选择“开启蓝牙”，时间设为 `18:30`，重复选择周一至周五。

程序启动或电脑唤醒后，会根据最近一条已生效规则校准蓝牙状态。

## 开机自启

设置窗口左下角有“开机自启”选项。只有勾选后，BlueTimer 才会写入 Windows 开机启动项。

如果需要手动清理自启项：

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "BlueTimer" -ErrorAction SilentlyContinue
```

## 蓝牙控制策略

BlueTimer 会按下面顺序尝试控制蓝牙：

1. Windows Bluetooth Radio API，相当于系统设置里的蓝牙开关。
2. `Enable-PnpDevice` / `Disable-PnpDevice`。
3. `pnputil /enable-device` / `pnputil /disable-device`。

在 Windows 11 上，部分 USB 蓝牙适配器不支持禁用 PnP 设备节点，会出现：

```text
Disable-PnpDevice : 常规故障
HRESULT 0x80041001
pnputil: 该操作系统产品不支持此命令
```

这种情况下应优先使用新版程序，因为新版会先走 Windows 蓝牙 Radio 开关，而不是优先禁用硬件节点。

## 已知注意事项

- 蓝牙开关动作可能需要几秒钟，USB 蓝牙适配器从关闭恢复到开启可能更慢。
- Windows 通知可能有延迟，这是通知中心和驱动响应共同造成的。
- 如果旧版本曾经把蓝牙设备节点禁用，建议先在 Windows 设置或设备管理器中手动恢复一次蓝牙。
- PyInstaller 打包程序可能被安全软件误报，正式分发建议代码签名。

## 故障排查

如果蓝牙适配器检测异常，可以运行诊断脚本：

```powershell
cd D:\啊\bluetimer
powershell -ExecutionPolicy Bypass -File .\tools\diagnose_bluetooth.ps1
```

如果“重新选择适配器”没有弹窗，确认托盘里旧进程已经退出后再打开新版程序。

如果开启蓝牙显示“验证超时”，可以先在 Windows 设置里手动打开蓝牙，确认适配器能正常恢复，再用新版测试。

## 开发运行

```powershell
cd D:\啊\bluetimer
.\.venv\Scripts\python.exe main.py
```

安装依赖：

```powershell
cd D:\啊\bluetimer
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 打包

主程序：

```powershell
cd D:\啊\bluetimer
.\.venv\Scripts\pyinstaller.exe --clean bluetimer.spec
```

Launcher：

```powershell
cd D:\啊\bluetimer\launcher
..\.venv\Scripts\pyinstaller.exe --clean launcher.spec
```

安装器：

```powershell
cd D:\啊\bluetimer\installer
..\.venv\Scripts\pyinstaller.exe --clean uninstall.spec
..\.venv\Scripts\pyinstaller.exe --clean setup.spec
```
