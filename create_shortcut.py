"""
Desktop Shortcut Creator for ApexClicker Pro.
Creates a Windows shortcut on the desktop with custom icon and pythonw target.
"""

import ctypes
import os
import subprocess
import sys


def notify_shell_icon_change():
    """Tells Windows Explorer to immediately refresh its icon cache and repainted desktop."""
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception:
        pass


def create_desktop_shortcut():
    if getattr(sys, "frozen", False):
        exe_path = sys.executable
        target_path = exe_path
        target_args = ""
        work_dir = os.path.dirname(exe_path)
        icon_path = exe_path
    else:
        workspace_dir = os.path.dirname(os.path.abspath(__file__))
        target_script = os.path.join(workspace_dir, "main.py")
        icon_path = os.path.join(workspace_dir, "assets", "icon.ico")
        python_dir = os.path.dirname(sys.executable)
        pythonw_path = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw_path):
            pythonw_path = sys.executable
        target_path = pythonw_path
        target_args = f'"{target_script}"'
        work_dir = workspace_dir

    ps_script = f"""
$wshell = New-Object -ComObject WScript.Shell
$desktopPaths = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('CommonDesktopDirectory')
)

$targetPath = '{target_path}'
$targetArgs = '{target_args}'
$iconPath = '{icon_path}'
$workDir = '{work_dir}'

$created = @()
foreach ($desk in $desktopPaths) {{
    if ($desk -and (Test-Path $desk)) {{
        $lnkPath = Join-Path $desk 'ApexClicker Pro.lnk'
        if (Test-Path $lnkPath) {{
            Remove-Item -Force $lnkPath -ErrorAction SilentlyContinue
        }}
        $shortcut = $wshell.CreateShortcut($lnkPath)
        $shortcut.TargetPath = $targetPath
        if ($targetArgs) {{
            $shortcut.Arguments = $targetArgs
        }}
        $shortcut.WorkingDirectory = $workDir
        $shortcut.IconLocation = ('{{0}},0' -f $iconPath)
        $shortcut.Description = 'ApexClicker Pro - Advanced Automation & Anti-Detection Auto Clicker'
        $shortcut.Save()
        $created += $lnkPath
    }}
}}

$created | ForEach-Object {{ Write-Output "SHORTCUT_CREATED: $_" }}
"""

    ps_file = os.path.join(workspace_dir, "_temp_create_shortcut.ps1")
    try:
        with open(ps_file, "w", encoding="utf-8") as f:
            f.write(ps_script)

        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
            capture_output=True,
            text=True,
            check=True,
        )
        # Flush Windows Shell icon cache
        notify_shell_icon_change()
        return res.stdout.strip()
    finally:
        if os.path.exists(ps_file):
            try:
                os.remove(ps_file)
            except Exception:
                pass


if __name__ == "__main__":
    out = create_desktop_shortcut()
    print(out)
