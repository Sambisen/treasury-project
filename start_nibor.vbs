' NIBOR Terminal Launcher
' Starts the application without showing a command prompt window

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Change to script directory
WshShell.CurrentDirectory = scriptDir

' Launch Python with main.py (hidden window)
WshShell.Run "pythonw main.py", 0, False
