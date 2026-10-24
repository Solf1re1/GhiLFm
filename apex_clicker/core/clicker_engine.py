"""
Clicker Engine.
The master background execution engine orchestrating:
- Extreme Burst & Precision clicking
- Multi-Point Sequences
- Pixel Color Reactive Triggers
- Visual Template / Image Matching
- Keyboard Auto-Presser / Key Spammer
with Process/Game Window Locking, Session Timers & Auto-Shutdown, and Click Ripples.
"""

import collections
import os
import threading
import time
import winsound
from typing import Dict, List, Any, Optional, Callable

from apex_clicker.core.input_driver import InputDriver, precise_sleep
from apex_clicker.core.humanizer import Humanizer
from apex_clicker.core.pixel_detector import PixelDetector
from apex_clicker.core.window_lock import WindowLockManager
from apex_clicker.core.scheduler import SessionScheduler
from apex_clicker.core.key_spammer import KeySpammer
from apex_clicker.core.template_matcher import TemplateMatcher


class ClickerEngine:
    """Master background worker orchestrating actions across all operating modes."""

    MODE_BURST = "BURST"
    MODE_SEQUENCE = "SEQUENCE"
    MODE_PIXEL = "PIXEL"
    MODE_TEMPLATE = "TEMPLATE"
    MODE_KEYSPAM = "KEYSPAM"

    def __init__(self):
        self.mode = self.MODE_BURST

        # State flags
        self._is_running = False
        self._is_paused = False
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Statistics
        self.total_clicks = 0
        self.current_cps = 0.0
        self._click_timestamps = collections.deque()
        self._stats_lock = threading.Lock()
        self._last_stats_calc = 0.0

        # Advanced Controls
        self.target_window = ""          # Empty = all/any window
        self.hotkey_mode = "TOGGLE"      # "TOGGLE" or "HOLD"
        self.sound_enabled = True
        self.ripple_enabled = True

        # Window exclusion (to avoid matching UI window in template search)
        self.exclude_rect: Optional[Tuple[int, int, int, int]] = None
        self.exclude_rect_getter: Optional[Callable[[], Optional[Tuple[int, int, int, int]]]] = None

        # Helper Engines
        self.scheduler = SessionScheduler()
        self.key_spammer = KeySpammer()

        # Callbacks
        self.on_status_change: Optional[Callable[[bool, bool, str], None]] = None
        self.on_click_update: Optional[Callable[[int, float], None]] = None
        self.on_ripple: Optional[Callable[[int, int], None]] = None

        # Mode configurations
        self.burst_config: Dict[str, Any] = {
            "target_mode": "CURRENT",
            "fixed_x": 0,
            "fixed_y": 0,
            "button": "left",
            "interval": 0.01,
            "repeat_limit": 0,
            "humanizer_enabled": False,
            "jitter_percent": 0.20,
            "jitter_radius": 3,
            "fatigue_enabled": False,
        }

        self.sequence_config: Dict[str, Any] = {
            "points": [],
            "repeat_count": 0,
            "humanizer_enabled": False,
        }

        self.pixel_config: Dict[str, Any] = {
            "x": 0,
            "y": 0,
            "target_color": (255, 0, 0),
            "condition": "MATCH",
            "tolerance": 15.0,
            "action": "CLICK_WHILE",
            "check_interval": 0.01,
            "button": "left",
            "cooldown": 0.5,
        }

        self.template_config: Dict[str, Any] = {
            "template_path": "",
            "confidence": 0.60,
            "match_mode": "similar",  # "exact" (0.95) or "similar" (0.60)
            "action": "CLICK",
            "button": "double",
            "smooth_move": True,      # Move over smoothly to target instead of instant jump
            "move_duration": 0.20,    # Glide duration in seconds
            "cooldown": 0.5,
            "search_interval": 0.1,
            "cached_template": None,
            "templates": [],  # Multi-template queue: List of dicts
            "flow_mode": "ANY",       # "ANY" (simultaneous search, default) or "SEQUENCE" (ordered 1->2->3)
            "on_not_found": "WAIT",   # "WAIT" (wait for target then proceed) or "SKIP" (go to next if not found)
            "loop_queue": True,       # Repeat sequence indefinitely
        }

        self.keyspam_config: Dict[str, Any] = {
            "keys": ["e"],
            "mode": "SIMULTANEOUS",  # "SIMULTANEOUS" or "CYCLE" or "HOLD"
            "interval": 0.1,
            "hold_duration": 0.02,
            "jitter_percent": 0.15,
        }

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def play_sound(self, sound_type: str):
        """Plays non-blocking audio cues if sound is enabled."""
        if not self.sound_enabled:
            return

        def _play():
            try:
                if sound_type == "start":
                    winsound.Beep(880, 70)
                elif sound_type == "stop":
                    winsound.Beep(440, 70)
                elif sound_type == "trigger":
                    winsound.Beep(1200, 50)
            except Exception:
                pass

        threading.Thread(target=_play, daemon=True).start()

    def start(self, mode: Optional[str] = None):
        """Starts the clicker worker thread."""
        if self._is_running:
            return

        if mode:
            self.mode = mode

        self._is_running = True
        self._is_paused = False
        self._stop_event.clear()
        self._pause_event.clear()

        with self._stats_lock:
            self.total_clicks = 0
            self.current_cps = 0.0
            self._click_timestamps.clear()

        # Initialize session scheduler
        self.scheduler.start()

        self.play_sound("start")

        if self.on_status_change:
            self.on_status_change(True, False, f"Running ({self.mode} Mode)")

        if self.mode == self.MODE_BURST:
            target_func = self._burst_worker
        elif self.mode == self.MODE_SEQUENCE:
            target_func = self._sequence_worker
        elif self.mode == self.MODE_PIXEL:
            target_func = self._pixel_worker
        elif self.mode == self.MODE_TEMPLATE:
            target_func = self._template_worker
        elif self.mode == self.MODE_KEYSPAM:
            target_func = self._keyspam_worker
        else:
            target_func = self._burst_worker

        self._worker_thread = threading.Thread(target=target_func, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Stops the clicker worker thread."""
        if not self._is_running:
            return

        self._is_running = False
        self._is_paused = False
        self._stop_event.set()
        self._pause_event.clear()

        self.scheduler.reset()

        # Release any held keys
        if self.mode == self.MODE_KEYSPAM:
            self.key_spammer.release_all(self.keyspam_config.get("keys", []))

        self.play_sound("stop")

        if self.on_status_change:
            self.on_status_change(False, False, "Stopped")

    def toggle(self):
        """Toggles between Start and Stop."""
        if self._is_running:
            self.stop()
        else:
            self.start()

    def toggle_pause(self):
        """Pauses or resumes ongoing clicks."""
        if not self._is_running:
            return

        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_event.set()
            self.scheduler.pause()
            if self.on_status_change:
                self.on_status_change(True, True, "Paused")
        else:
            self._pause_event.clear()
            self.scheduler.start()
            if self.on_status_change:
                self.on_status_change(True, False, f"Running ({self.mode} Mode)")

    def _record_click(self):
        """Tracks click count and micro-throttled sliding-window CPS calculation."""
        now = time.perf_counter()
        self.total_clicks += 1
        self._click_timestamps.append(now)

        # Micro-throttle sliding window and UI callback to ~30 FPS to reduce lock contention and CPU load
        if now - self._last_stats_calc >= 0.033:
            self._last_stats_calc = now
            with self._stats_lock:
                while self._click_timestamps and (now - self._click_timestamps[0] > 1.0):
                    self._click_timestamps.popleft()
                self.current_cps = float(len(self._click_timestamps))

            if self.on_click_update:
                self.on_click_update(self.total_clicks, self.current_cps)

    def get_exclude_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Returns the screen rectangle (x, y, w, h) of the UI to exclude from image searching."""
        if self.exclude_rect_getter:
            try:
                rect = self.exclude_rect_getter()
                if rect:
                    return rect
            except Exception:
                pass
        return self.exclude_rect

    def _execute_click(
        self,
        button: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        smooth: bool = True,
        duration: float = 0.20,
    ):
        """Executes a single mouse click/action and triggers visual ripple."""
        if x is not None and y is not None:
            # Target specified: move over smoothly, yield for hover/focus, and perform solid click
            InputDriver.move_and_click(
                x,
                y,
                button=button,
                hold_time=0.035,
                smooth=smooth,
                duration=duration,
                cancel_check=lambda: self._stop_event.is_set(),
            )
            click_x, click_y = x, y
        else:
            click_x, click_y = InputDriver.get_cursor_pos()
            btn = button.lower()
            if btn == "left":
                InputDriver.click("left")
            elif btn == "right":
                InputDriver.click("right")
            elif btn == "middle":
                InputDriver.click("middle")
            elif btn == "double":
                InputDriver.double_click("left")
            elif btn == "triple":
                InputDriver.triple_click("left")
            elif btn == "scroll_up":
                InputDriver.scroll(1)
            elif btn == "scroll_down":
                InputDriver.scroll(-1)
            elif btn == "hold_left":
                InputDriver.mouse_down("left")
            else:
                InputDriver.click("left")

        # Visual click ripple notification
        if self.ripple_enabled and self.on_ripple:
            try:
                self.on_ripple(click_x, click_y)
            except Exception:
                pass

        try:
            self._record_click()
        except Exception as e:
            print(f"Error recording click: {e}")

    def _check_safety_and_scheduler(self) -> bool:
        """
        Validates target window lock and timer expiration.
        Returns False if clicks should be skipped or halted.
        """
        # Check window/game lock
        if self.target_window and not WindowLockManager.is_target_active(self.target_window):
            precise_sleep(0.04)
            return False

        # Check session scheduler duration
        if self.scheduler.is_expired():
            self._stop_event.set()
            threading.Thread(target=self.scheduler.execute_completion_action, daemon=True).start()
            return False

        return True

    def _burst_worker(self):
        """High-speed or customized burst clicking loop."""
        cfg = self.burst_config
        target_mode = cfg.get("target_mode", "CURRENT")
        fixed_x = cfg.get("fixed_x", 0)
        fixed_y = cfg.get("fixed_y", 0)
        button = cfg.get("button", "left")
        base_interval = max(0.0005, cfg.get("interval", 0.01))
        repeat_limit = cfg.get("repeat_limit", 0)
        human_enabled = cfg.get("humanizer_enabled", False)
        jitter_pct = cfg.get("jitter_percent", 0.20)
        jitter_rad = cfg.get("jitter_radius", 3)
        fatigue_enabled = cfg.get("fatigue_enabled", False)

        clicks_done = 0
        fatigue_counter = 0
        fatigue_target = 60

        try:
            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    precise_sleep(0.02)
                    continue

                if not self._check_safety_and_scheduler():
                    continue

                # Determine click coordinate
                if target_mode == "FIXED":
                    tx, ty = fixed_x, fixed_y
                    if human_enabled and jitter_rad > 0:
                        tx, ty = Humanizer.get_jittered_point(tx, ty, jitter_rad)
                    self._execute_click(button, tx, ty)
                else:
                    if human_enabled and jitter_rad > 0:
                        cx, cy = InputDriver.get_cursor_pos()
                        jx, jy = Humanizer.get_jittered_point(cx, cy, jitter_rad)
                        self._execute_click(button, jx, jy)
                    else:
                        self._execute_click(button)

                clicks_done += 1
                if repeat_limit > 0 and clicks_done >= repeat_limit:
                    break

                interval = base_interval
                if human_enabled and jitter_pct > 0:
                    interval = Humanizer.get_randomized_delay(base_interval, jitter_pct)

                if human_enabled and fatigue_enabled:
                    fatigue_counter += 1
                    if fatigue_counter >= fatigue_target:
                        fatigue_counter = 0
                        fatigue_target = int(60 + 40 * (time.time() % 1.0))
                        interval += 0.20

                precise_sleep(interval)
        except Exception as e:
            print(f"Error in burst worker: {e}")
        finally:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "Finished")

    def _sequence_worker(self):
        """Iterates through multi-point sequence items."""
        cfg = self.sequence_config
        points: List[Dict[str, Any]] = cfg.get("points", [])
        repeat_count = cfg.get("repeat_count", 0)
        human_enabled = cfg.get("humanizer_enabled", False)

        if not points:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "No points in sequence")
            return

        loops_done = 0
        try:
            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    precise_sleep(0.02)
                    continue

                for pt in points:
                    if self._stop_event.is_set():
                        break
                    while self._pause_event.is_set() and not self._stop_event.is_set():
                        precise_sleep(0.02)

                    while not self._check_safety_and_scheduler() and not self._stop_event.is_set():
                        precise_sleep(0.04)

                    tx = pt.get("x", 0)
                    ty = pt.get("y", 0)
                    btn = pt.get("button", "left")
                    delay = max(0.001, pt.get("delay", 0.1))
                    jitter_rad = pt.get("jitter_radius", 0)
                    smooth = pt.get("smooth_move", False)
                    move_dur = pt.get("move_duration", 0.25)

                    if human_enabled and jitter_rad > 0:
                        tx, ty = Humanizer.get_jittered_point(tx, ty, jitter_rad)

                    if smooth:
                        Humanizer.move_smoothly(
                            tx,
                            ty,
                            duration=move_dur,
                            overshoot=human_enabled,
                            cancel_check=lambda: self._stop_event.is_set(),
                        )
                    else:
                        InputDriver.set_cursor_pos(tx, ty)

                    self._execute_click(btn)

                    if human_enabled:
                        delay = Humanizer.get_randomized_delay(delay, 0.20)

                    precise_sleep(delay)

                loops_done += 1
                if repeat_count > 0 and loops_done >= repeat_count:
                    break
        finally:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "Finished Sequence")

    def _pixel_worker(self):
        """Continuously monitors pixel at (x, y) and executes configured action."""
        cfg = self.pixel_config
        px = cfg.get("x", 0)
        py = cfg.get("y", 0)
        target_color = cfg.get("target_color", (255, 0, 0))
        condition = cfg.get("condition", "MATCH")
        tolerance = cfg.get("tolerance", 15.0)
        action = cfg.get("action", "CLICK_WHILE")
        check_interval = max(0.005, cfg.get("check_interval", 0.01))
        btn = cfg.get("button", "left")
        cooldown = max(0.05, cfg.get("cooldown", 0.5))

        try:
            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    precise_sleep(0.02)
                    continue

                if not self._check_safety_and_scheduler():
                    continue

                triggered = PixelDetector.check_trigger(
                    px, py, target_color, condition, tolerance
                )

                if triggered:
                    self.play_sound("trigger")
                    if action == "CLICK_ONCE":
                        self._execute_click(btn, px, py)
                        precise_sleep(cooldown)
                    elif action == "CLICK_WHILE":
                        self._execute_click(btn, px, py)
                        precise_sleep(check_interval)
                else:
                    precise_sleep(check_interval)
        finally:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "Pixel trigger stopped")

    def _template_worker(self):
        """Searches screen for template image(s) and triggers click on detection."""
        InputDriver.ensure_desktop_access()
        cfg = self.template_config
        t_path = cfg.get("template_path", "")
        conf = cfg.get("confidence", 0.80)
        btn = cfg.get("button", "left")
        cooldown = max(0.05, cfg.get("cooldown", 0.5))
        s_interval = max(0.02, cfg.get("search_interval", 0.1))

        # Build list of active candidates: (img_ndarray, confidence_thresh, metadata)
        active_candidates: List[Tuple[Any, float, Any]] = []
        raw_templates = cfg.get("templates", [])

        if raw_templates:
            for tpl in raw_templates:
                if tpl.get("enabled", True):
                    p = tpl.get("path", "")
                    if p and os.path.exists(p):
                        img = tpl.get("cached")
                        if img is None:
                            img = TemplateMatcher.load_template_file(p)
                            tpl["cached"] = img
                        if img is not None:
                            t_conf = tpl.get("confidence", conf)
                            active_candidates.append((img, t_conf, tpl))

        # Fallback to single template_path if no multi-template items are active
        if not active_candidates and t_path and os.path.exists(t_path):
            img = cfg.get("cached_template")
            if img is None:
                img = TemplateMatcher.load_template_file(t_path)
                cfg["cached_template"] = img
            if img is not None:
                active_candidates.append((img, conf, {"name": os.path.basename(t_path), "path": t_path}))

        if not active_candidates:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "No active template images loaded")
            return

        flow_mode = cfg.get("flow_mode", "SEQUENCE")
        on_not_found = cfg.get("on_not_found", "WAIT")
        loop_queue = cfg.get("loop_queue", True)
        smooth_move = cfg.get("smooth_move", True)
        move_dur = cfg.get("move_duration", 0.20)

        try:
            curr_step = 0
            num_targets = len(active_candidates)

            while not self._stop_event.is_set():
                if self._pause_event.is_set():
                    precise_sleep(0.02)
                    continue

                if not self._check_safety_and_scheduler():
                    continue

                exclude = self.get_exclude_rect()

                if flow_mode == "ANY" or num_targets <= 1:
                    # Search screen for ANY active candidate template (simultaneous match)
                    match = TemplateMatcher.find_any_template(
                        active_candidates,
                        exclude_rect=exclude,
                    )
                    if match:
                        cx, cy, score, meta = match
                        self.play_sound("trigger")
                        self._execute_click(btn, cx, cy, smooth=smooth_move, duration=move_dur)
                        precise_sleep(cooldown)
                    else:
                        precise_sleep(s_interval)
                else:
                    # Ordered sequence execution (Step 1 -> Step 2 -> Step 3)
                    target_candidate = active_candidates[curr_step]
                    match = TemplateMatcher.find_any_template(
                        [target_candidate],
                        exclude_rect=exclude,
                    )
                    if match:
                        cx, cy, score, meta = match
                        self.play_sound("trigger")
                        self._execute_click(btn, cx, cy, smooth=smooth_move, duration=move_dur)
                        precise_sleep(cooldown)

                        curr_step += 1
                        if curr_step >= num_targets:
                            if loop_queue:
                                curr_step = 0
                            else:
                                break
                    else:
                        # Target not currently visible on screen
                        if on_not_found == "SKIP":
                            # "Go to next if not found": advance immediately to next target in sequence
                            curr_step += 1
                            if curr_step >= num_targets:
                                if loop_queue:
                                    curr_step = 0
                                else:
                                    break
                            precise_sleep(s_interval)
                        else:
                            # "Wait for target then proceed": keep polling until this target appears
                            precise_sleep(s_interval)
        finally:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "Template search finished")

    def _keyspam_worker(self):
        """Keyboard auto-presser execution loop."""
        cfg = self.keyspam_config
        keys: List[str] = cfg.get("keys", ["e"])
        spam_mode = cfg.get("mode", "SIMULTANEOUS")
        base_interval = max(0.005, cfg.get("interval", 0.1))
        hold_dur = cfg.get("hold_duration", 0.02)
        jitter_pct = cfg.get("jitter_percent", 0.15)

        if not keys:
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "No keys specified")
            return

        try:
            if spam_mode == "HOLD":
                for k in keys:
                    self.key_spammer.hold_key(k)
                while not self._stop_event.is_set():
                    if self._pause_event.is_set():
                        self.key_spammer.release_all(keys)
                        while self._pause_event.is_set() and not self._stop_event.is_set():
                            precise_sleep(0.05)
                        for k in keys:
                            self.key_spammer.hold_key(k)
                    if not self._check_safety_and_scheduler():
                        continue
                    self._record_click()
                    precise_sleep(0.05)
            else:
                while not self._stop_event.is_set():
                    if self._pause_event.is_set():
                        precise_sleep(0.02)
                        continue

                    if not self._check_safety_and_scheduler():
                        continue

                    if spam_mode == "SIMULTANEOUS":
                        for k in keys:
                            self.key_spammer.press_key(k, hold_dur)
                        self._record_click()
                    elif spam_mode == "CYCLE":
                        for k in keys:
                            if self._stop_event.is_set():
                                break
                            self.key_spammer.press_key(k, hold_dur)
                            self._record_click()
                            intv = base_interval
                            if jitter_pct > 0:
                                intv = Humanizer.get_randomized_delay(base_interval, jitter_pct)
                            precise_sleep(intv)
                        continue

                    intv = base_interval
                    if jitter_pct > 0:
                        intv = Humanizer.get_randomized_delay(base_interval, jitter_pct)
                    precise_sleep(intv)
        finally:
            self.key_spammer.release_all(keys)
            self._is_running = False
            if self.on_status_change:
                self.on_status_change(False, False, "Key spammer finished")
