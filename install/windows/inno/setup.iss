; Inno Setup script to install ReqStudio from source
; Requires Inno Setup 6.x

#define MyAppName "ReqStudio"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Y10K Software Engineering"
#define MyAppURL "https://y10k-tech.github.io/reqstudio/"
#define RootDir "..\\.."

[Setup]
AppId={{6C46F86A-7A68-4F01-9F6C-3F0F5A2C6B32}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={userappdata}\\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=reqstudio-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy the repository content into the app directory
Source: "{#RootDir}\\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
; Exclude typical VCS/venv/build artifacts
Source: "{#RootDir}\\.git\\*"; DestDir: "{app}\\.git"; Flags: recursesubdirs createallsubdirs; Tasks: never; Excludes: "*" 

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{sys}\WindowsPowerShell\\v1.0\\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File \"{app}\\install\\windows\\launch_reqstudio.ps1\""; IconFilename: "{app}\\media\\reqstudio_logo.ico"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{sys}\WindowsPowerShell\\v1.0\\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File \"{app}\\install\\windows\\launch_reqstudio.ps1\""; IconFilename: "{app}\\media\\reqstudio_logo.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
; Post-install: create venv and install project
Filename: "{sys}\WindowsPowerShell\\v1.0\\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File \"{app}\\install\\windows\\install_reqstudio.ps1\""; Flags: runhidden; StatusMsg: "Setting up Python environment..."

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\\v1.0\\powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File \"{app}\\install\\windows\\uninstall_reqstudio.ps1\" -KeepVenv"; Flags: runhidden

