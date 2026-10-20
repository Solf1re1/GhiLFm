"""
Keyboard Auto-Presser & Key Spammer Engine.
Simulates high-speed key tapping, key holding, and multi-key sequences with customizable intervals
and humanized delay variances.
"""

import time
from typing import List, Dict, Any, Optional
import pynput
from pynput import keyboard
from apex_clicker.core.input_driver import precise_sleep
from apex_clicker.core.humanizer import Humanizer


def parse_key_string(key_name: str) -> Any:
    """Converts a string representation into a pynput key or KeyCode."""
    clean = key_name.strip().lower()
    if hasattr(keyboard.Key, clean):
        return getattr(keyboard.Key, clean)

    special_map = {
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "shift": keyboard.Key.shift,
        "space": keyboard.Key.space,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "backspace": keyboard.Key.backspace,
        "esc": keyboard.Key.esc,
    }
    if clean in special_map:
        return special_map[clean]

    if len(clean) == 1:
        return clean
    return clean


class KeySpammer:
    """Executes keyboard spamming cycles."""

    def __init__(self):
        self._controller = keyboard.Controller()

    def press_key(self, key_str: str, hold_duration: float = 0.02):
        """Taps a key (down + hold + up)."""
        k = parse_key_string(key_str)
        try:
            self._controller.press(k)
            if hold_duration > 0:
                precise_sleep(hold_duration)
            self._controller.release(k)
        except Exception:
            pass

    def hold_key(self, key_str: str):
        """Holds down a key without releasing."""
        k = parse_key_string(key_str)
        try:
            self._controller.press(k)
        except Exception:
            pass

    def release_key(self, key_str: str):
        """Releases a held key."""
        k = parse_key_string(key_str)
        try:
            self._controller.release(k)
        except Exception:
            pass

    def release_all(self, keys: List[str]):
        """Safety release for all registered keys."""
        for k in keys:
            self.release_key(k)
