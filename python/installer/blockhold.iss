; Inno Setup script for the BLOCKHOLD Windows installer.
;
; Build the game first (cd python; pyinstaller blockhold.spec --noconfirm), then:
;   ISCC.exe /DMyAppVersion=1.9.0 installer\blockhold.iss
; GitHub Actions does this for every release (.github/workflows/release.yml).
;
; Installs for the current user by default (no admin prompt), so the in-game updater can
; run a new installer silently. Your saves and settings live in %USERPROFILE%\.blockhold
; and are kept when you uninstall or update.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "BLOCKHOLD"
#define MyAppExe "BLOCKHOLD.exe"
#define MyAppURL "https://github.com/masterxxstabs/killcraft-remake"

[Setup]
AppId={{6F1C2B7E-4A9D-4E3B-8C51-2D7A0B9E4F13}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=masterxxstabs
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=BLOCKHOLD-Setup-{#MyAppVersion}
SetupIconFile=blockhold.ico
UninstallDisplayIcon={app}\{#MyAppExe}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; clear out the previous version's engine files so nothing stale is left behind
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\BLOCKHOLD\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
; also runs after a silent install, so the game starts again after an in-game update
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall; Check: ShouldLaunch

[Code]
{ /NOLAUNCH on the command line = don't start the game afterwards (used by the build checks) }
function ShouldLaunch: Boolean;
var
  I: Integer;
begin
  Result := True;
  for I := 1 to ParamCount do
    if CompareText(ParamStr(I), '/NOLAUNCH') = 0 then
      Result := False;
end;
