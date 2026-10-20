"""
Screen Coordinate and Pixel Color Picker Helper.
Provides countdown-based or hotkey-based capture of screen coordinates and colors.
"""

import time
import threading
from typing import Callable, Optional
from apex_clicker.core.input_driver import InputDriver
from apex_clicker.core.pixel_detector import PixelDetector


class CoordinatePickerHelper:
    """Helper for sampling screen coordinates and RGB colors."""

    @staticmethod
    def capture_cursor() -> tuple[int, int]:
        """Captures immediate screen coordinates."""
        return InputDriver.get_cursor_pos()

    @staticmethod
    def capture_pixel_at_cursor() -> tuple[int, int, tuple[int, int, int]]:
        """Captures current cursor position and RGB color."""
        x, y = InputDriver.get_cursor_pos()
        rgb = PixelDetector.get_pixel_color(x, y)
        return (x, y, rgb)

    @classmethod
    def capture_after_delay(
        cls,
        delay_seconds: float,
        on_countdown: Optional[Callable[[int], None]],
        on_complete: Callable[[int, int], None],
    ):
        """Runs a background countdown then samples position."""
        def _worker():
            remaining = int(delay_seconds)
            while remaining > 0:
                if on_countdown:
                    on_countdown(remaining)
                time.sleep(1.0)
                remaining -= 1

            pos = cls.capture_cursor()
            on_complete(pos[0], pos[1])

        threading.Thread(target=_worker, daemon=True).start()
