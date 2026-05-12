#define MyAppName "BlueTimer"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "BlueTimer"
#define MyAppExeName "BlueTimer.exe"

[Setup]
AppId={{9F51B7E8-3D96-4D60-AF9C-5E1A5F95A0F2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=BlueTimer_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："; Flags: unchecked

[Files]
Source: "..\dist\BlueTimer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\BlueTimer"; Filename: "{app}\BlueTimer.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 BlueTimer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\BlueTimer"; Filename: "{app}\BlueTimer.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\BlueTimer.exe"; Description: "启动 BlueTimer"; Flags: nowait postinstall skipifsilent runascurrentuser

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\BlueTimer"
