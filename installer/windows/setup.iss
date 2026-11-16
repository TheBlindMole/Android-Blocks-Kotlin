; Script do Inno Setup 6 para criar o instalador do DroidBlocks Studio no Windows.
; Normalmente chamado por installer/build_executable.py, que define as variaveis abaixo.
; Uso manual: ISCC.exe /DAppVersion=1.1.0 /DSourceExe=..\..\dist\DroidBlocksStudio.exe setup.iss

#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif
#ifndef SourceExe
  #define SourceExe "..\..\dist\DroidBlocksStudio.exe"
#endif
#ifndef IconFile
  #define IconFile "..\..\build\icons\droidblocks.ico"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist"
#endif

[Setup]
AppId={{6F0B7A52-3C1D-4E8B-9C55-2D1F0B7DB10C}
AppName=DroidBlocks Studio
AppVersion={#AppVersion}
AppPublisher=DroidBlocks
DefaultDirName={autopf}\DroidBlocks Studio
DefaultGroupName=DroidBlocks Studio
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#OutputDir}
OutputBaseFilename=DroidBlocksStudio-Setup
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\DroidBlocksStudio.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "DroidBlocksStudio.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\DroidBlocks Studio"; Filename: "{app}\DroidBlocksStudio.exe"
Name: "{autodesktop}\DroidBlocks Studio"; Filename: "{app}\DroidBlocksStudio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DroidBlocksStudio.exe"; Description: "{cm:LaunchProgram,DroidBlocks Studio}"; Flags: nowait postinstall skipifsilent
