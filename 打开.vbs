' 静默启动后端并打开浏览器（无黑窗口）
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
root = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = root
sh.Run "cmd /c python run.py --daemon --open", 0, False
