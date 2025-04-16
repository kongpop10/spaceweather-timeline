Set oWS = WScript.CreateObject("WScript.Shell")

' Create Start Menu shortcut
sStartMenuPath = oWS.SpecialFolders("StartMenu") & "\Programs\Space Weather Timeline.lnk"
Set oLink = oWS.CreateShortcut(sStartMenuPath)
oLink.TargetPath = oWS.CurrentDirectory & "\launch_spaceweather_app.bat"
oLink.WorkingDirectory = oWS.CurrentDirectory
oLink.Description = "Launch Space Weather Timeline App"
oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,43"
oLink.Save

WScript.Echo "Shortcut created successfully in the Start Menu Programs folder."
