"""
Window and Game Process Binding Manager.
Locks clicker activity to a designated window or game process, automatically pausing
when the user alt-tabs or focuses another application.
"""

import ctypes
from ctypes import wintypes
import time
from typing import List, Tuple, Dict, Optional
import psutil

user32 = ctypes.windll.user32


class WindowLockManager:
    """Detects and matches active foreground windows for process locking with high-speed caching."""

    _last_check_time = 0.0
    _cached_result = True
    _cached_hwnd = 0
    _cached_process = ""
    _cached_title = ""
    _pid_cache: Dict[int, str] = {}

    @classmethod
    def get_foreground_info(cls) -> Dict[str, str]:
        """Returns HWND, Title, and Process Name of current foreground window."""
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {"hwnd": 0, "title": "", "process": ""}

        if hwnd == cls._cached_hwnd and cls._cached_process:
            return {"hwnd": hwnd, "title": cls._cached_title, "process": cls._cached_process}

        # Window title
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value

        # Process name with PID cache
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pid_val = pid.value
        pname = cls._pid_cache.get(pid_val)
        if not pname:
            try:
                p = psutil.Process(pid_val)
                pname = p.name()
                if len(cls._pid_cache) > 256:
                    cls._pid_cache.clear()
                cls._pid_cache[pid_val] = pname
            except Exception:
                pname = ""

        cls._cached_hwnd = hwnd
        cls._cached_title = title
        cls._cached_process = pname
        return {"hwnd": hwnd, "title": title, "process": pname}

    @classmethod
    def list_visible_windows(cls) -> List[Tuple[str, str]]:
        """
        Enumerates all visible top-level windows.
        Returns list of (display_label, match_identifier).
        """
        results = []

        def enum_windows_callback(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if title:
                        pid = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        pid_val = pid.value
                        pname = cls._pid_cache.get(pid_val)
                        if not pname:
                            try:
                                p = psutil.Process(pid_val)
                                pname = p.name()
                                cls._pid_cache[pid_val] = pname
                            except Exception:
                                pname = ""
                        if pname:
                            label = f"{title[:45]} ({pname})"
                            results.append((label, pname))
                        else:
                            results.append((title[:50], title))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb = WNDENUMPROC(enum_windows_callback)
        user32.EnumWindows(cb, 0)
        return results

    @classmethod
    def is_target_active(cls, target_identifier: str, throttle_sec: float = 0.05) -> bool:
        """
        Checks if foreground window matches target_identifier.
        Target can be a process name ('RobloxPlayerBeta.exe') or title substring.
        Empty or 'ANY' target always returns True.
        """
        target = target_identifier.strip().lower()
        if not target or target in ("any", "any active window", "all windows"):
            return True

        now = time.perf_counter()
        if now - cls._last_check_time < throttle_sec:
            return cls._cached_result

        cls._last_check_time = now
        info = cls.get_foreground_info()
        title = info["title"].lower()
        process = info["process"].lower()

        is_match = (target in process) or (target in title)
        cls._cached_result = is_match
        return is_match
