Set shell = CreateObject("WScript.Shell")
appDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.Run """" & appDir & "\launch_server.bat" & """", 0, False
WScript.Sleep 3000
shell.Run "http://localhost:8501", 1, False
