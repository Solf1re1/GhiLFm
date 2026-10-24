"""
Global Hotkey Manager.
Listens for global keystrokes in the background (even when the app is minimized or backgrounded)
and triggers actions like Start/Stop, Pause, Coordinate Pick, Pixel Color Sampling, and Macro Record.
Supports single keys and multi-key combinations with modifiers (e.g. Ctrl+F6, Alt+F8, etc.).
"""

import ctypes
from typing import Dict, Callable, Optional, Set
import pynput
from pynput import keyboard

# Win32 Virtual Key codes for reliable modifier detection
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_RWIN = 0x5C


class HotkeyManager:
    """Manages system-wide global hotkeys with modifier key support."""

    def __init__(self):
        # Default hotkey mappings (Ctrl+F6 start/stop toggle)
        self.bindings: Dict[str, str] = {
            "toggle": "ctrl+f6",
            "pause": "ctrl+f7",
            "pick_coord": "ctrl+f8",
            "sample_pixel": "ctrl+f9",
            "macro_toggle": "ctrl+f10",
        }

        self.callbacks: Dict[str, Optional[Callable[[], None]]] = {
            "toggle": None,
            "pause": None,
            "pick_coord": None,
            "sample_pixel": None,
            "macro_toggle": None,
        }

        self.release_callbacks: Dict[str, Optional[Callable[[], None]]] = {
            "toggle": None,
            "pause": None,
            "pick_coord": None,
            "sample_pixel": None,
            "macro_toggle": None,
        }

        self._listener: Optional[keyboard.Listener] = None
        self._is_listening = False
        self._user32 = ctypes.windll.user32

        # Modifier tracking
        self._pressed_keys: Set[str] = set()
        self._triggered_actions: Set[str] = set()

    def set_callback(self, action: str, callback: Callable[[], None]):
        """Binds a callable to an action name."""
        if action in self.callbacks:
            self.callbacks[action] = callback

    def set_release_callback(self, action: str, callback: Callable[[], None]):
        """Binds a release callable to an action name."""
        if action in self.release_callbacks:
            self.release_callbacks[action] = callback

    def set_hotkey(self, action: str, key_name: str):
        """
        Rebinds an action to a new key combination.
        e.g. 'ctrl+f6', 'alt+f8', 'f6', 'ctrl+shift+x'
        Enforces strict uniqueness so no other action shares the same hotkey.
        """
        if action in self.bindings:
            # Clean and canonicalize
            parts = [p.strip().lower() for p in key_name.split("+") if p.strip()]
            new_combo = "+".join(parts)
            # Ensure no collision with another action
            for act, existing_combo in list(self.bindings.items()):
                if act != action and existing_combo == new_combo and new_combo != "":
                    self.bindings[act] = ""
            self.bindings[action] = new_combo

    def get_hotkey_display(self, action: str) -> str:
        """Returns formatted display string, e.g. 'Ctrl+F6'."""
        raw = self.bindings.get(action, "")
        if not raw:
            return ""
        parts = raw.split("+")
        formatted = []
        for p in parts:
            if p == "win":
                formatted.append("Win")
            elif p == "ctrl":
                formatted.append("Ctrl")
            elif p == "alt":
                formatted.append("Alt")
            elif p == "shift":
                formatted.append("Shift")
            elif p.startswith("f") and p[1:].isdigit():
                formatted.append(p.upper())
            elif p == "*":
                formatted.append("*")
            else:
                formatted.append(p.capitalize())
        return "+".join(formatted)

    def _is_modifier_physically_down(self, vk: int) -> bool:
        """Queries Windows hardware keyboard state directly."""
        try:
            return bool(self._user32.GetAsyncKeyState(vk) & 0x8000)
        except Exception:
            return False

    def _normalize_key(self, key) -> str:
        """Translates a pynput key event to our canonical string format."""
        try:
            if isinstance(key, keyboard.Key):
                name = key.name.lower()
                if name in ("ctrl_l", "ctrl_r"):
                    return "ctrl"
                elif name in ("alt_l", "alt_r", "alt_gr"):
                    return "alt"
                elif name in ("shift_l", "shift_r"):
                    return "shift"
                elif name in ("cmd", "cmd_l", "cmd_r"):
                    return "win"
                return name
            elif isinstance(key, keyboard.KeyCode):
                if key.vk in (VK_LWIN, VK_RWIN):
                    return "win"
                if key.vk == 0x6A or key.char == "*":
                    return "*"
                if key.char:
                    return key.char.lower()
                elif key.vk is not None:
                    # Windows virtual key codes (F1-F12 are 0x70 to 0x7B)
                    if 0x70 <= key.vk <= 0x7B:
                        return f"f{key.vk - 0x70 + 1}"
                    return f"vk_{key.vk}"
        except Exception:
            pass
        return ""

    def _get_current_modifiers(self) -> Set[str]:
        """Returns currently active modifier names."""
        mods = set()
        if "win" in self._pressed_keys or self._is_modifier_physically_down(VK_LWIN) or self._is_modifier_physically_down(VK_RWIN):
            mods.add("win")
        if "ctrl" in self._pressed_keys or self._is_modifier_physically_down(VK_CONTROL):
            mods.add("ctrl")
        if "alt" in self._pressed_keys or self._is_modifier_physically_down(VK_MENU):
            mods.add("alt")
        if "shift" in self._pressed_keys or self._is_modifier_physically_down(VK_SHIFT):
            mods.add("shift")
        return mods

    def _build_combination_string(self, primary_key: str) -> str:
        """Constructs canonical combination string like 'win+*' or 'ctrl+f6'."""
        mods = self._get_current_modifiers()
        parts = []
        if "win" in mods and primary_key != "win":
            parts.append("win")
        if "ctrl" in mods and primary_key != "ctrl":
            parts.append("ctrl")
        if "alt" in mods and primary_key != "alt":
            parts.append("alt")
        if "shift" in mods and primary_key != "shift":
            parts.append("shift")

        if primary_key not in ("win", "ctrl", "alt", "shift"):
            parts.append(primary_key)

        return "+".join(parts)

    def _on_key_press(self, key):
        """Processes key press events."""
        if not self._is_listening:
            return

        norm_key = self._normalize_key(key)
        if not norm_key:
            return

        self._pressed_keys.add(norm_key)

        # Ignore standalone modifier presses for action triggering
        if norm_key in ("win", "ctrl", "alt", "shift"):
            return

        current_combo = self._build_combination_string(norm_key)

        for action, bound_key in self.bindings.items():
            if current_combo == bound_key:
                # Debounce: prevent repeat storm while key is held down
                if action not in self._triggered_actions:
                    self._triggered_actions.add(action)
                    cb = self.callbacks.get(action)
                    if cb:
                        try:
                            cb()
                        except Exception as err:
                            print(f"Error in hotkey callback [{action}]: {err}")

    def _on_key_release(self, key):
        """Processes key release events."""
        norm_key = self._normalize_key(key)
        if not norm_key:
            return

        self._pressed_keys.discard(norm_key)

        # Release triggered actions associated with this key
        # Reset actions when the primary key or any modifier is released
        actions_to_clear = []
        for action, bound_key in self.bindings.items():
            parts = bound_key.split("+")
            if norm_key in parts:
                actions_to_clear.append(action)

        for act in actions_to_clear:
            if act in self._triggered_actions:
                self._triggered_actions.discard(act)
                rel_cb = self.release_callbacks.get(act)
                if rel_cb:
                    try:
                        rel_cb()
                    except Exception as err:
                        print(f"Error in hotkey release callback [{act}]: {err}")

    def start(self):
        """Starts listening for global hotkeys."""
        if self._is_listening:
            return

        self._is_listening = True
        self._pressed_keys.clear()
        self._triggered_actions.clear()

        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Stops the global hotkey listener."""
        self._is_listening = False
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        self._pressed_keys.clear()
        self._triggered_actions.clear()
