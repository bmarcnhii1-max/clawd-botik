[Setup]
AppId={{8A3B2C1D-4E5F-4A6B-8C7D-9E0F1A2B3C4D}
AppName=Clawd
AppVersion=1.0.9
DefaultDirName={autopf}\Clawd
DefaultGroupName=Clawd
DisableProgramGroupPage=yes
OutputBaseFilename=Clawd-Setup
SetupIconFile=clawd.ico
UninstallDisplayIcon={app}\Clawd.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "en"; MessagesFile: "compiler:Languages\English.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\Clawd.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Clawd"; Filename: "{app}\Clawd.exe"
Name: "{autodesktop}\Clawd"; Filename: "{app}\Clawd.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Clawd.exe"; Description: "Launch Clawd"; Flags: nowait postinstall skipifsilent
