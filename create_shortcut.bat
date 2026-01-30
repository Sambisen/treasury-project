@echo off
:: Creates a desktop shortcut for NIBOR Terminal
:: Run this once after setup

set SCRIPT_DIR=%~dp0
set SHORTCUT_NAME=NIBOR Terminal
set DESKTOP=%USERPROFILE%\Desktop

:: Create VBS script to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%start_nibor.vbs" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "NIBOR Calculation Terminal" >> "%TEMP%\CreateShortcut.vbs"
:: Use Python icon as default (or custom icon if exists)
if exist "%SCRIPT_DIR%assets\icon.ico" (
    echo oLink.IconLocation = "%SCRIPT_DIR%assets\icon.ico" >> "%TEMP%\CreateShortcut.vbs"
) else (
    for %%I in (pythonw.exe) do echo oLink.IconLocation = "%%~$PATH:I" >> "%TEMP%\CreateShortcut.vbs"
)
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

:: Run VBS script
cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo ========================================
echo  Shortcut created on Desktop!
echo  Look for "NIBOR Terminal" icon
echo ========================================
echo.
pause
