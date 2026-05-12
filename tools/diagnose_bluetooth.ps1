$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

Write-Host "== BlueTimer Bluetooth diagnostics =="
Write-Host "PowerShell:" $PSVersionTable.PSVersion
Write-Host ""

Write-Host "== Get-PnpDevice -Class Bluetooth -PresentOnly =="
Get-PnpDevice -Class Bluetooth -PresentOnly -ErrorAction SilentlyContinue |
    Select-Object Class, FriendlyName, Status, InstanceId |
    Format-List

Write-Host ""
Write-Host "== Possible hardware Bluetooth adapters =="
Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.Class -eq 'Bluetooth' -or $_.FriendlyName -match '(?i)bluetooth') -and
        ($_.InstanceId -match '^(USB|PCI|ACPI)\\' -or $_.FriendlyName -match '(?i)(adapter|radio|wireless bluetooth|bluetooth usb)')
    } |
    Select-Object Class, FriendlyName, Status, InstanceId |
    Format-List
