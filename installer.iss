#define MyAppName "Control de Lotes"
#define MyAppExeName "control_lotes.exe"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.8"
#endif

[Setup]
AppId={{39F7F1CA-DE22-4DAB-8D90-BF7DBFC09A85}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Control de Lotes
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=assets\icon.ico
OutputDir=installer_output
OutputBaseFilename=control_lotes_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "dist\control_lotes.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent
