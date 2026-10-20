"""
Humanizer & Anti-Detection Engine.
Simulates natural human mouse movement (Cubic Bezier curves, variable easing),
spatial coordinate jitter (Gaussian dispersion), delay randomization,
and natural fatigue micro-pauses.
"""

import math
import random
import time
from typing import List, Tuple
from apex_clicker.core.input_driver import InputDriver, precise_sleep


class Humanizer:
    """Anti-bot human simulation algorithms for clicks and cursor motion."""

    @staticmethod
    def get_jittered_point(
        target_x: int, target_y: int, jitter_radius: int = 4
    ) -> Tuple[int, int]:
        """
        Applies a 2D Gaussian distribution jitter to the target coordinate.
        Keeps clicks within jitter_radius while creating organic clustering.
        """
        if jitter_radius <= 0:
            return (target_x, target_y)

        # Standard deviation so ~99% of clicks are within jitter_radius
        sigma = jitter_radius / 3.0
        dx = random.gauss(0, sigma)
        dy = random.gauss(0, sigma)

        # Clamp distance to jitter_radius
        dist = math.hypot(dx, dy)
        if dist > jitter_radius:
            scale = jitter_radius / dist
            dx *= scale
            dy *= scale

        return (int(round(target_x + dx)), int(round(target_y + dy)))

    @staticmethod
    def get_randomized_delay(base_delay: float, jitter_percent: float = 0.25) -> float:
        """
        Randomizes click interval around base_delay.
        jitter_percent: fraction of variation, e.g. 0.20 = ±20% variation.
        """
        if base_delay <= 0 or jitter_percent <= 0:
            return max(0.0001, base_delay)

        # Triangular / Gaussian distribution for natural variance
        variance = base_delay * jitter_percent
        randomized = random.gauss(base_delay, variance / 2.5)
        # Ensure it stays within reasonable bounds
        min_bound = max(0.0001, base_delay * (1.0 - jitter_percent))
        max_bound = base_delay * (1.0 + jitter_percent)
        return max(min_bound, min(max_bound, randomized))

    @staticmethod
    def _bezier_point(
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        t: float,
    ) -> Tuple[float, float]:
        """Cubic Bezier formula."""
        u = 1.0 - t
        tt = t * t
        uu = u * u
        uuu = uu * u
        ttt = tt * t

        x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
        y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
        return (x, y)

    @classmethod
    def move_smoothly(
        cls,
        end_x: int,
        end_y: int,
        duration: float = 0.25,
        overshoot: bool = True,
        cancel_check: callable = None,
    ):
        """
        Moves the mouse from current position to (end_x, end_y) along
        a natural Bezier curve with human-like acceleration and deceleration.
        """
        start_x, start_y = InputDriver.get_cursor_pos()
        dist = math.hypot(end_x - start_x, end_y - start_y)
        if dist < 3 or duration <= 0:
            InputDriver.set_cursor_pos(end_x, end_y)
            return

        # Adaptive duration based on distance if not fixed
        actual_duration = max(0.05, duration)

        # Generate control points perpendicular to direction
        angle = math.atan2(end_y - start_y, end_x - start_x)
        perp = angle + math.pi / 2.0

        # Random lateral deviation (sway)
        max_deviation = min(80.0, dist * 0.25)
        dev1 = random.uniform(-max_deviation, max_deviation)
        dev2 = random.uniform(-max_deviation, max_deviation)

        # Control points at ~30% and ~70% along the trajectory
        p0 = (float(start_x), float(start_y))
        p3 = (float(end_x), float(end_y))

        # Add optional slight overshoot
        if overshoot and dist > 50 and random.random() < 0.35:
            overshoot_dist = random.uniform(3, 12)
            p3 = (
                p3[0] + math.cos(angle) * overshoot_dist,
                p3[1] + math.sin(angle) * overshoot_dist,
            )

        mid1_x = start_x + (end_x - start_x) * 0.33 + math.cos(perp) * dev1
        mid1_y = start_y + (end_y - start_y) * 0.33 + math.sin(perp) * dev1

        mid2_x = start_x + (end_x - start_x) * 0.67 + math.cos(perp) * dev2
        mid2_y = start_y + (end_y - start_y) * 0.67 + math.sin(perp) * dev2

        p1 = (mid1_x, mid1_y)
        p2 = (mid2_x, mid2_y)

        # Number of steps (~120 updates per second)
        steps = max(10, int(actual_duration * 120))
        dt = actual_duration / steps

        monitors = InputDriver.get_screen_monitors()
        start_time = time.perf_counter()
        for i in range(1, steps + 1):
            if cancel_check and cancel_check():
                return

            raw_t = i / steps
            # Smooth Ease-In-Out curve (sinusoidal)
            eased_t = (1.0 - math.cos(raw_t * math.pi)) / 2.0

            x, y = cls._bezier_point(p0, p1, p2, p3, eased_t)
            ix, iy = InputDriver.clamp_to_monitors(int(round(x)), int(round(y)), monitors)
            InputDriver.set_cursor_pos(ix, iy)
            try:
                InputDriver._user32.mouse_event(0x0001, 0, 0, 0, 0)
            except Exception:
                pass

            target_time = start_time + i * dt
            sleep_time = target_time - time.perf_counter()
            if sleep_time > 0:
                precise_sleep(sleep_time)

        # Snap to exact target at end
        InputDriver.set_cursor_pos(end_x, end_y)
