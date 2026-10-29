"""
Macro Recorder and Playback Engine.
Captures mouse clicks, moves, scrolls, and keystrokes with millisecond precision,
and provides variable-speed looped playback.
"""

import json
import threading
import time
from typing import List, Dict, Any, Optional, Callable
import pynput
from pynput import mouse, keyboard
from apex_clicker.core.input_driver import precise_sleep


def serialize_key(key: Any) -> Dict[str, Any]:
    """Converts a pynput key object into a serializable dict."""
    if isinstance(key, keyboard.Key):
        return {"type": "special", "name": key.name}
    elif isinstance(key, keyboard.KeyCode):
        return {"type": "char", "char": key.char, "vk": key.vk}
    else:
        return {"type": "unknown", "str": str(key)}


def deserialize_key(data: Dict[str, Any]) -> Any:
    """Restores a pynput key object from serialized dict."""
    ktype = data.get("type")
    if ktype == "special":
        name = data.get("name")
        return getattr(keyboard.Key, name, None)
    elif ktype == "char":
        char = data.get("char")
        vk = data.get("vk")
        if char:
            return keyboard.KeyCode.from_char(char)
        elif vk is not None:
            return keyboard.KeyCode.from_vk(vk)
    return None


class MacroEngine:
    """Records and plays back mouse and keyboard events."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self._is_recording = False
        self._is_playing = False
        self._stop_playback_flag = threading.Event()
        self._record_start_time = 0.0
        self._last_event_time = 0.0

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None

        self._mouse_controller = mouse.Controller()
        self._keyboard_controller = keyboard.Controller()

        self._playback_thread: Optional[threading.Thread] = None
        self.stop_hotkey: str = "ctrl+f10"

        # Callbacks
        self.on_record_event: Optional[Callable[[int], None]] = None
        self.on_state_change: Optional[Callable[[bool, bool], None]] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def set_stop_hotkey(self, combo_str: str):
        """Sets the hotkey string to filter out during recording (e.g. 'ctrl+f10')."""
        self.stop_hotkey = combo_str.lower().strip()

    def _is_hotkey_trigger_key(self, key: Any) -> bool:
        """Determines if a key is the primary trigger (F10) for macro recording toggle."""
        try:
            if isinstance(key, keyboard.Key):
                name = key.name.lower()
                if name == "f10":
                    return True
                parts = self.stop_hotkey.split("+")
                if len(parts) > 0 and name == parts[-1]:
                    return True
            elif isinstance(key, keyboard.KeyCode):
                if key.vk == 121:  # VK_F10
                    return True
        except Exception:
            pass
        return False

    def _sanitize_events_list(self, evs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cleans macro events list:
        1. Strips leading release events of modifiers/hotkey keys (user lifting fingers after starting).
        2. Strips trailing key press/release events of modifiers/hotkey keys (user pressing Ctrl+F10 to stop).
        3. Strips any stray F10 keystrokes anywhere in the macro.
        """
        if not evs:
            return []

        def is_macro_hotkey_part(event):
            if event.get("kind") not in ("key_press", "key_release"):
                return False
            k = event.get("key", {})
            name = (k.get("name") or "").lower()
            vk = k.get("vk")
            if name in ("f10", "ctrl", "ctrl_l", "ctrl_r", "menu", "alt", "alt_l", "alt_r", "shift", "shift_l", "shift_r", "cmd", "cmd_l", "cmd_r"):
                return True
            if vk == 121:
                return True
            return False

        # 1. Remove leading key releases of modifiers/trigger
        start_idx = 0
        while start_idx < len(evs) and evs[start_idx].get("kind") == "key_release" and is_macro_hotkey_part(evs[start_idx]):
            start_idx += 1
        cleaned = list(evs[start_idx:])

        # 2. Remove trailing key presses/releases of modifiers/trigger
        while cleaned and is_macro_hotkey_part(cleaned[-1]):
            cleaned.pop()

        # 3. Filter out any internal F10 events
        final_events = []
        for e in cleaned:
            if e.get("kind") in ("key_press", "key_release"):
                k = e.get("key", {})
                name = (k.get("name") or "").lower()
                vk = k.get("vk")
                if name == "f10" or vk == 121:
                    continue
            final_events.append(e)

        return final_events

    def start_recording(self, record_mouse_moves: bool = False):
        """Starts capturing mouse and keyboard events."""
        if self._is_recording or self._is_playing:
            return

        self.events = []
        self._is_recording = True
        self._record_start_time = time.perf_counter()
        self._last_event_time = self._record_start_time

        def on_move(x, y):
            if not self._is_recording or not record_mouse_moves:
                return
            now = time.perf_counter()
            # Throttle mouse moves to at most 60 updates/sec to prevent bloated files
            if now - self._last_event_time < 0.016:
                return
            dt = now - self._last_event_time
            self._last_event_time = now
            self.events.append({"kind": "mouse_move", "x": x, "y": y, "delay": dt})
            if self.on_record_event:
                self.on_record_event(len(self.events))

        def on_click(x, y, button, pressed):
            if not self._is_recording:
                return
            now = time.perf_counter()
            dt = now - self._last_event_time
            self._last_event_time = now
            bname = button.name if hasattr(button, "name") else str(button)
            self.events.append(
                {
                    "kind": "mouse_click",
                    "x": x,
                    "y": y,
                    "button": bname,
                    "pressed": pressed,
                    "delay": dt,
                }
            )
            if self.on_record_event:
                self.on_record_event(len(self.events))

        def on_scroll(x, y, dx, dy):
            if not self._is_recording:
                return
            now = time.perf_counter()
            dt = now - self._last_event_time
            self._last_event_time = now
            self.events.append(
                {"kind": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy, "delay": dt}
            )
            if self.on_record_event:
                self.on_record_event(len(self.events))

        def on_key_press(key):
            if not self._is_recording:
                return
            # Filter out F10/stop hotkey so it is never recorded into macro
            if self._is_hotkey_trigger_key(key):
                return
            now = time.perf_counter()
            dt = now - self._last_event_time
            self._last_event_time = now
            self.events.append(
                {
                    "kind": "key_press",
                    "key": serialize_key(key),
                    "delay": dt,
                }
            )
            if self.on_record_event:
                self.on_record_event(len(self.events))

        def on_key_release(key):
            if not self._is_recording:
                return
            # Filter out F10/stop hotkey release
            if self._is_hotkey_trigger_key(key):
                return
            now = time.perf_counter()
            dt = now - self._last_event_time
            self._last_event_time = now
            self.events.append(
                {
                    "kind": "key_release",
                    "key": serialize_key(key),
                    "delay": dt,
                }
            )
            if self.on_record_event:
                self.on_record_event(len(self.events))

        self._mouse_listener = mouse.Listener(
            on_move=on_move if record_mouse_moves else None,
            on_click=on_click,
            on_scroll=on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release,
        )

        self._mouse_listener.start()
        self._keyboard_listener.start()

        if self.on_state_change:
            self.on_state_change(self._is_recording, self._is_playing)

    def stop_recording(self):
        """Stops the recording session and cleans modifier/hotkey artifacts."""
        if not self._is_recording:
            return

        self._is_recording = False
        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        # Sanitize trailing hotkey events (e.g. Ctrl pressed when hitting Ctrl+F10 to stop)
        self.events = self._sanitize_events_list(self.events)
        if self.on_record_event:
            self.on_record_event(len(self.events))

        if self.on_state_change:
            self.on_state_change(self._is_recording, self._is_playing)

    def start_playback(
        self,
        speed_multiplier: float = 1.0,
        repeat_count: int = 1,  # 0 or negative = infinite
        on_complete: Optional[Callable[[], None]] = None,
    ):
        """Plays recorded macro events in a background thread."""
        if self._is_playing or self._is_recording or not self.events:
            return

        # Sanitize prior to playback to ensure no trailing toggle hotkeys exist
        self.events = self._sanitize_events_list(self.events)
        if not self.events:
            return

        self._is_playing = True
        self._stop_playback_flag.clear()

        def playback_worker():
            try:
                loop = 0
                speed = max(0.01, speed_multiplier)

                while not self._stop_playback_flag.is_set():
                    loop += 1
                    for event in self.events:
                        if self._stop_playback_flag.is_set():
                            break

                        # Wait event delay adjusted by speed multiplier
                        delay = event.get("delay", 0.0) / speed
                        if delay > 0:
                            precise_sleep(delay)

                        kind = event.get("kind")
                        if kind == "mouse_move":
                            self._mouse_controller.position = (
                                event["x"],
                                event["y"],
                            )
                        elif kind == "mouse_click":
                            self._mouse_controller.position = (
                                event["x"],
                                event["y"],
                            )
                            b_str = event.get("button", "left").lower()
                            btn = mouse.Button.left
                            if "right" in b_str:
                                btn = mouse.Button.right
                            elif "middle" in b_str:
                                btn = mouse.Button.middle

                            if event.get("pressed", True):
                                self._mouse_controller.press(btn)
                            else:
                                self._mouse_controller.release(btn)
                        elif kind == "mouse_scroll":
                            self._mouse_controller.position = (
                                event["x"],
                                event["y"],
                            )
                            self._mouse_controller.scroll(
                                event.get("dx", 0), event.get("dy", 0)
                            )
                        elif kind == "key_press":
                            k = deserialize_key(event.get("key", {}))
                            if k is not None:
                                try:
                                    self._keyboard_controller.press(k)
                                except Exception:
                                    pass
                        elif kind == "key_release":
                            k = deserialize_key(event.get("key", {}))
                            if k is not None:
                                try:
                                    self._keyboard_controller.release(k)
                                except Exception:
                                    pass

                    if repeat_count > 0 and loop >= repeat_count:
                        break
            finally:
                self._is_playing = False
                time.sleep(0.150)  # Grace period so simulated keys don't trigger hotkeys
                if self.on_state_change:
                    self.on_state_change(self._is_recording, self._is_playing)
                if on_complete:
                    on_complete()

        self._playback_thread = threading.Thread(
            target=playback_worker, daemon=True
        )
        self._playback_thread.start()

        if self.on_state_change:
            self.on_state_change(self._is_recording, self._is_playing)

    def stop_playback(self):
        """Stops ongoing playback."""
        if not self._is_playing:
            return
        self._stop_playback_flag.set()
        self._is_playing = False
        if self.on_state_change:
            self.on_state_change(self._is_recording, self._is_playing)

    def save_to_file(self, file_path: str):
        """Saves current macro events to a JSON file."""
        self.events = self._sanitize_events_list(self.events)
        data = {
            "version": "1.0",
            "event_count": len(self.events),
            "events": self.events,
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, file_path: str):
        """Loads macro events from a JSON file and removes any hotkey artifacts."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.events = self._sanitize_events_list(data.get("events", []))
