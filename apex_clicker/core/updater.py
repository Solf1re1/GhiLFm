"""
In-App Auto-Updater for ApexClicker Pro.
Queries GitHub Releases API, checks for newer semantic versions,
downloads release assets with progress tracking, and applies seamless in-place updates.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from typing import Optional, Dict, Any, Tuple, Callable


class AppUpdater:
    """Manages GitHub Releases version checking, asset downloading, and self-updating."""

    REPO_OWNER = "Solf1re1"
    REPO_NAME = "GhiLFm"
    API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

    @classmethod
    def parse_version(cls, version_str: str) -> Tuple[int, ...]:
        """Parses a version string like 'v1.0.1' or '1.0.1' into a comparable tuple of ints."""
        clean = version_str.strip().lstrip("vV")
        parts = []
        for p in clean.split("."):
            num = "".join(c for c in p if c.isdigit())
            if num:
                parts.append(int(num))
            else:
                parts.append(0)
        return tuple(parts)

    @classmethod
    def check_for_update(cls, current_version: str) -> Optional[Dict[str, Any]]:
        """
        Queries GitHub API for the latest release.
        Returns release dictionary if a newer version is available, else None.
        """
        try:
            req = urllib.request.Request(
                cls.API_URL,
                headers={
                    "User-Agent": "ApexClicker-Pro-Updater",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=7) as response:
                if response.status != 200:
                    return None
                data = json.loads(response.read().decode("utf-8"))

            latest_tag = data.get("tag_name", "").strip()
            if not latest_tag:
                return None

            latest_ver = cls.parse_version(latest_tag)
            curr_ver = cls.parse_version(current_version)

            if latest_ver > curr_ver:
                # Find appropriate binary asset (.exe or -Instant.zip)
                assets = data.get("assets", [])
                best_asset = None

                # If running as directory distribution, prefer the Instant.zip package
                is_dir_dist = not getattr(sys, "frozen", False) or not sys.executable.endswith(".exe")
                # Look for matching executable or zip
                for a in assets:
                    name = a.get("name", "")
                    if name == "ApexClicker.exe":
                        best_asset = a
                        break
                    elif name.endswith(".exe") and not best_asset:
                        best_asset = a

                return {
                    "tag_name": latest_tag,
                    "title": data.get("name", latest_tag),
                    "body": data.get("body", "").strip(),
                    "html_url": data.get("html_url", ""),
                    "asset_name": best_asset.get("name", "") if best_asset else "",
                    "download_url": best_asset.get("browser_download_url", "") if best_asset else "",
                    "size": best_asset.get("size", 0) if best_asset else 0,
                    "all_assets": assets,
                }

            return None
        except Exception as e:
            print(f"Update check error: {e}")
            return None

    @classmethod
    def download_asset(
        cls,
        download_url: str,
        dest_path: str,
        progress_callback: Optional[Callable[[float, int, int], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> bool:
        """
        Downloads a file from download_url to dest_path with chunked streaming and progress reporting.
        progress_callback(fraction_0_to_1, downloaded_bytes, total_bytes)
        """
        try:
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "ApexClicker-Pro-Updater"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB chunks

                with open(dest_path, "wb") as f:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            return False
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            fraction = (downloaded / total_size) if total_size > 0 else 0.0
                            progress_callback(min(1.0, fraction), downloaded, total_size)

            return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0
        except Exception as e:
            print(f"Download error: {e}")
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            return False

    @classmethod
    def apply_update_and_restart(cls, new_binary_path: str):
        """
        Executes a detached PowerShell updater script that terminates running ApexClicker processes,
        safely replaces the target executable (with rename fallback for OS file lock bypass),
        cleans up staging files, and relaunches the updated executable.
        """
        if getattr(sys, "frozen", False):
            target_exe = os.path.abspath(sys.executable)
        else:
            # Running from source: update C:\moddingtools\ApexClicker.exe or dist\ApexClicker.exe
            if os.path.exists(r"C:\moddingtools\ApexClicker.exe"):
                target_exe = r"C:\moddingtools\ApexClicker.exe"
            elif os.path.exists(r"C:\moddingtools\ApexClicker\ApexClicker.exe"):
                target_exe = r"C:\moddingtools\ApexClicker\ApexClicker.exe"
            else:
                target_exe = os.path.abspath(sys.argv[0])

        target_dir = os.path.dirname(os.path.abspath(target_exe))
        target_pid = os.getpid()

        ps1_path = os.path.join(tempfile.gettempdir(), f"apex_updater_{int(time.time())}.ps1")
        ps_script = f"""
# Step 1: Wait for current process and stop lingering ApexClicker instances
Start-Sleep -Milliseconds 400
Get-Process -Name 'ApexClicker' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 600

# Step 2: Attempt replacement with retries and rename fallback
$replaced = $false
for ($i = 0; $i -lt 20; $i++) {{
    try {{
        Copy-Item -LiteralPath '{new_binary_path}' -Destination '{target_exe}' -Force -ErrorAction Stop
        $replaced = $true
        break
    }} catch {{
        try {{
            $bak = '{target_exe}.old'
            if (Test-Path -LiteralPath $bak) {{
                Remove-Item -LiteralPath $bak -Force -ErrorAction SilentlyContinue
            }}
            Move-Item -LiteralPath '{target_exe}' -Destination $bak -Force -ErrorAction Stop
            Copy-Item -LiteralPath '{new_binary_path}' -Destination '{target_exe}' -Force -ErrorAction Stop
            Remove-Item -LiteralPath $bak -Force -ErrorAction SilentlyContinue
            $replaced = $true
            break
        }} catch {{
            Start-Sleep -Seconds 1
        }}
    }}
}}

# Step 3: Cleanup and relaunch
if ($replaced) {{
    Remove-Item -LiteralPath '{new_binary_path}' -Force -ErrorAction SilentlyContinue
    Start-Process -FilePath '{target_exe}' -WorkingDirectory '{target_dir}'
}}

Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
"""
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

        # Launch detached PowerShell process with proper non-window flags
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", ps1_path,
            ],
            creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )

        # Gracefully terminate current process
        os._exit(0)
