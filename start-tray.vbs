' start-tray.vbs
' Duplo clique pra iniciar o rgb-hub na bandeja sem janela de console.
' Copie ou crie um atalho deste arquivo na pasta shell:startup pra auto-start.

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' caminho do pythonw.exe (mesmo diretorio que python.exe)
pythonDir = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312")
If Not fso.FolderExists(pythonDir) Then
    ' fallback: tenta encontrar via PATH
    pythonDir = ""
End If

If pythonDir <> "" Then
    pythonw = pythonDir & "\pythonw.exe"
Else
    pythonw = "pythonw.exe"
End If

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

WshShell.Run """" & pythonw & """ """ & scriptDir & "\tray.py""", 0, False
