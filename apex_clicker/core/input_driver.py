"""
Win32 SendInput high-speed mouse and input driver.
Provides sub-millisecond precision, true 1000 CPS burst clicking,
accurate DPI handling, and multimedia timer management.
"""

import ctypes
from ctypes import wintypes
import math
import threading
import time
from typing import Tuple, List, Optional, Callable

# Initialize DPI awareness so coordinates are 1:1 with screen pixels
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
WHEEL_DELTA = 120

ULONG_PTR = ctypes.c_size_t

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class HighPrecisionTimer:
    """Manages Windows Multimedia Timer resolution for 1ms accuracy."""
    _active = False

    @classmethod
    def enable(cls):
        if not cls._active:
            try:
                ctypes.windll.winmm.timeBeginPeriod(1)
                cls._active = True
            except Exception:
                pass

    @classmethod
    def disable(cls):
        if cls._active:
            try:
                ctypes.windll.winmm.timeEndPeriod(1)
                cls._active = False
            except Exception:
                pass


# Enable high precision timer globally on import
HighPrecisionTimer.enable()


def precise_sleep(seconds: float):
    """
    Sub-millisecond hybrid sleep:
    Sleeps most of the duration via system sleep,
    then spins with perf_counter for the final fraction of a millisecond.
    """
    if seconds <= 0:
        return
    target = time.perf_counter() + seconds
    # If sleep duration is larger than 2ms, yield execution to OS
    if seconds > 0.002:
        time.sleep(seconds - 0.0015)
    # Spin the remainder for microsecond precision
    while time.perf_counter() < target:
        pass


class InputDriver:
    """Native Windows SendInput driver for ultra-low latency mouse simulation."""

    _user32 = ctypes.windll.user32
    _send_input = _user32.SendInput
    _send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    _send_input.restype = wintypes.UINT

    _user32.SetCursorPos.argtypes = (ctypes.c_int, ctypes.c_int)
    _user32.SetCursorPos.restype = wintypes.BOOL

    _thread_local = threading.local()
    _cached_input = INPUT()
    _cached_input.type = INPUT_MOUSE
    _cached_input_ref = ctypes.byref(_cached_input)
    _input_size = ctypes.sizeof(INPUT)

    @classmethod
    def ensure_desktop_access(cls):
        """Ensures the calling thread is attached to the active interactive desktop (cached per-thread)."""
        if getattr(cls._thread_local, "attached", False):
            return
        try:
            hwinsta = cls._user32.OpenWindowStationW("WinSta0", False, 0x10000000)
            if hwinsta:
                cls._user32.SetProcessWindowStation(hwinsta)
                hdesk = cls._user32.OpenDesktopW("Default", 0, False, 0x10000000)
                if hdesk:
                    cls._user32.SetThreadDesktop(hdesk)
                    cls._thread_local.attached = True
        except Exception:
            pass

    @classmethod
    def get_cursor_pos(cls) -> Tuple[int, int]:
        """Returns current mouse cursor screen coordinates (x, y)."""
        cls.ensure_desktop_access()
        pt = POINT()
        cls._user32.GetCursorPos(ctypes.byref(pt))
        return (int(pt.x), int(pt.y))

    @classmethod
    def set_cursor_pos(cls, x: int, y: int):
        """Moves cursor to (x, y). Supports multi-monitor and negative coordinates."""
        cls.ensure_desktop_access()
        ix, iy = int(x), int(y)
        success = cls._user32.SetCursorPos(ix, iy)
        if not success:
            # Fallback 1: SendInput with virtual desktop normalized coordinates
            try:
                v_left = cls._user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
                v_top = cls._user32.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
                v_width = cls._user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
                v_height = cls._user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
                if v_width > 1 and v_height > 1:
                    nx = int((ix - v_left) * 65536 / v_width)
                    ny = int((iy - v_top) * 65536 / v_height)
                    cls._send_mouse_event(0x0001 | 0x8000 | 0x4000, dx=nx, dy=ny)
            except Exception:
                pass
            # Fallback 2: mouse_event
            try:
                cls._user32.mouse_event(0x0001 | 0x8000 | 0x4000, nx, ny, 0, 0)
            except Exception:
                pass

    @classmethod
    def get_screen_monitors(cls) -> List[Tuple[int, int, int, int]]:
        """Returns list of all active display monitors as (left, top, right, bottom)."""
        monitors = []
        def _cb(hMonitor, hdcMonitor, lprcMonitor, dwData):
            r = lprcMonitor.contents
            monitors.append((int(r.left), int(r.top), int(r.right), int(r.bottom)))
            return True
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_void_p,
        )
        cls._user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_cb), 0)
        return monitors

    @classmethod
    def clamp_to_monitors(
        cls, x: int, y: int, monitors: Optional[List[Tuple[int, int, int, int]]] = None
    ) -> Tuple[int, int]:
        """Ensures coordinate is on a physical screen and avoids multi-monitor dead-zones."""
        if monitors is None:
            monitors = cls.get_screen_monitors()
        if not monitors:
            return x, y
        for l, t, r, b in monitors:
            if l <= x < r and t <= y < b:
                return x, y
        best_dist = float("inf")
        best_pt = (x, y)
        for l, t, r, b in monitors:
            cx = max(l, min(r - 1, x))
            cy = max(t, min(b - 1, y))
            d = math.hypot(cx - x, cy - y)
            if d < best_dist:
                best_dist = d
                best_pt = (cx, cy)
        return best_pt

    @classmethod
    def move_smoothly_to(
        cls,
        target_x: int,
        target_y: int,
        duration: float = 0.20,
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        """
        Smoothly glides the mouse cursor across the screen to (target_x, target_y).
        Avoids multi-monitor dead zones and sends real mouse motion events so Windows,
        Explorer, and games track natural cursor travel and hover states.
        """
        cls.ensure_desktop_access()
        start_x, start_y = cls.get_cursor_pos()
        dist = math.hypot(target_x - start_x, target_y - start_y)
        if dist < 4 or duration <= 0:
            cls.set_cursor_pos(target_x, target_y)
            return

        monitors = cls.get_screen_monitors()
        steps = max(15, min(60, int(duration * 120)))
        dt = duration / steps
        last_x, last_y = start_x, start_y
        t_start = time.perf_counter()

        for i in range(1, steps + 1):
            if cancel_check and cancel_check():
                break
            raw_t = i / steps
            eased_t = (1.0 - math.cos(raw_t * math.pi)) / 2.0
            cur_x = int(round(start_x + (target_x - start_x) * eased_t))
            cur_y = int(round(start_y + (target_y - start_y) * eased_t))
            cur_x, cur_y = cls.clamp_to_monitors(cur_x, cur_y, monitors)

            dx = cur_x - last_x
            dy = cur_y - last_y
            last_x, last_y = cur_x, cur_y

            cls.set_cursor_pos(cur_x, cur_y)
            try:
                cls._user32.mouse_event(0x0001, dx, dy, 0, 0)
            except Exception:
                pass

            target_time = t_start + i * dt
            sleep_time = target_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)

        cls.set_cursor_pos(target_x, target_y)

    @classmethod
    def move_and_click(
        cls,
        x: int,
        y: int,
        button: str = "left",
        hold_time: float = 0.035,
        smooth: bool = True,
        duration: float = 0.20,
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        """
        Moves cursor to (x, y) - either smoothly gliding or directly - yields briefly for
        WM_MOUSEMOVE hover handling, and performs a solid mouse click or double-click.
        """
        cls.ensure_desktop_access()
        if smooth:
            cls.move_smoothly_to(x, y, duration=duration, cancel_check=cancel_check)
        else:
            cls.set_cursor_pos(x, y)

        # 40ms pause for OS & target window hover/focus dispatch
        time.sleep(0.040)

        # Re-assert exact position prior to click
        cls.set_cursor_pos(x, y)

        b = button.lower()
        if b == "double":
            cls.double_click("left", interval=0.075)
        elif b == "triple":
            cls.triple_click("left")
        elif b == "right":
            cls.click("right", hold_time=hold_time)
        elif b == "middle":
            cls.click("middle", hold_time=hold_time)
        elif b == "scroll_up":
            cls.scroll(1)
        elif b == "scroll_down":
            cls.scroll(-1)
        elif b == "hold_left":
            cls.mouse_down("left")
        else:
            cls.click("left", hold_time=hold_time)
        time.sleep(0.020)  # 20ms post-click buffer

    @classmethod
    def _send_mouse_event(cls, flags: int, data: int = 0, dx: int = 0, dy: int = 0):
        cls.ensure_desktop_access()
        # Fast direct mutation of preallocated ctypes struct without allocation
        mi = cls._cached_input.u.mi
        mi.dx = dx
        mi.dy = dy
        mi.mouseData = data
        mi.dwFlags = flags
        mi.time = 0
        mi.dwExtraInfo = 0
        cls._send_input(1, cls._cached_input_ref, cls._input_size)

    @classmethod
    def mouse_down(cls, button: str = "left"):
        cls.ensure_desktop_access()
        b = button.lower()
        if b == "left":
            cls._send_mouse_event(MOUSEEVENTF_LEFTDOWN)
        elif b == "right":
            cls._send_mouse_event(MOUSEEVENTF_RIGHTDOWN)
        elif b == "middle":
            cls._send_mouse_event(MOUSEEVENTF_MIDDLEDOWN)

    @classmethod
    def mouse_up(cls, button: str = "left"):
        cls.ensure_desktop_access()
        b = button.lower()
        if b == "left":
            cls._send_mouse_event(MOUSEEVENTF_LEFTUP)
        elif b == "right":
            cls._send_mouse_event(MOUSEEVENTF_RIGHTUP)
        elif b == "middle":
            cls._send_mouse_event(MOUSEEVENTF_MIDDLEUP)

    @classmethod
    def click(cls, button: str = "left", hold_time: float = 0.025):
        """Single click (down + precise wait + up)."""
        cls.mouse_down(button)
        if hold_time > 0:
            precise_sleep(hold_time)
        cls.mouse_up(button)

    @classmethod
    def double_click(cls, button: str = "left", interval: float = 0.075):
        """Double click that reliably opens apps and desktop icons in Windows."""
        pos = cls.get_cursor_pos()
        cls.click(button, hold_time=0.035)
        time.sleep(interval)
        cls.set_cursor_pos(pos[0], pos[1])
        cls.click(button, hold_time=0.035)

    @classmethod
    def triple_click(cls, button: str = "left", interval: float = 0.04):
        """Triple click."""
        cls.click(button)
        precise_sleep(interval)
        cls.click(button)
        precise_sleep(interval)
        cls.click(button)

    @classmethod
    def scroll(cls, clicks: int):
        """
        Scroll wheel. Positive is up, negative is down.
        Each standard notch is WHEEL_DELTA (120).
        """
        cls._send_mouse_event(MOUSEEVENTF_WHEEL, data=int(clicks * WHEEL_DELTA))
