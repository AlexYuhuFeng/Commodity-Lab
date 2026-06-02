!include "MUI2.nsh"

Name "Hedge Lab Terminal"
OutFile "dist/HedgeLabInstaller.exe"
InstallDir "$PROGRAMFILES64\Hedge Lab Terminal"
RequestExecutionLevel user

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist/Commodity-Lab.exe"
    CreateDirectory "$SMPROGRAMS\Hedge Lab Terminal"
    CreateShortCut "$SMPROGRAMS\Hedge Lab Terminal\Hedge Lab Terminal.lnk" "$INSTDIR\Commodity-Lab.exe"
    CreateShortCut "$DESKTOP\Hedge Lab Terminal.lnk" "$INSTDIR\Commodity-Lab.exe"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\Commodity-Lab.exe"
    Delete "$SMPROGRAMS\Hedge Lab Terminal\Hedge Lab Terminal.lnk"
    Delete "$DESKTOP\Hedge Lab Terminal.lnk"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$SMPROGRAMS\Hedge Lab Terminal"
    RMDir "$INSTDIR"
SectionEnd
