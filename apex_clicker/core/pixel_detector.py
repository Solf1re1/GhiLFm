"""
Pixel & Color Detector.
Ultra-fast screen color sampling via Windows GDI and Delta-E / Euclidean color distance matching.
Supports instant color picking and condition evaluation.
"""

import ctypes
import math
from typing import Tuple, Optional

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class PixelDetector:
    """Fast screen pixel sampler and color matcher."""

    @staticmethod
    def get_pixel_color(x: int, y: int) -> Tuple[int, int, int]:
        """
        Samples the RGB color of the pixel at (x, y) on the screen.
        Uses native Windows GDI GetPixel for maximum speed.
        """
        hdc = user32.GetDC(0)
        try:
            color_ref = gdi32.GetPixel(hdc, int(x), int(y))
            # COLORREF is 0x00BBGGRR
            r = color_ref & 0xFF
            g = (color_ref >> 8) & 0xFF
            b = (color_ref >> 16) & 0xFF
            return (r, g, b)
        finally:
            user32.ReleaseDC(0, hdc)

    @staticmethod
    def color_to_hex(r: int, g: int, b: int) -> str:
        """Converts RGB tuple to #RRGGBB string."""
        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
        """Converts #RRGGBB or RRGGBB string to (R, G, B) tuple."""
        clean = hex_str.strip().lstrip("#")
        if len(clean) == 3:
            clean = "".join([c * 2 for c in clean])
        if len(clean) != 6:
            return (255, 255, 255)
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        return (r, g, b)

    @staticmethod
    def color_distance(
        c1: Tuple[int, int, int], c2: Tuple[int, int, int]
    ) -> float:
        """
        Calculates weighted Euclidean color distance (approximating human eye perception):
        Reduces green sensitivity, balances red and blue.
        Returns distance from 0.0 (identical) to ~765.0.
        """
        dr = c1[0] - c2[0]
        dg = c1[1] - c2[1]
        db = c1[2] - c2[2]
        # Weighted Euclidean distance
        # 30% Red, 59% Green, 11% Blue perceptual weighting
        return math.sqrt(0.3 * (dr ** 2) + 0.59 * (dg ** 2) + 0.11 * (db ** 2))

    @classmethod
    def matches(
        cls,
        c1: Tuple[int, int, int],
        c2: Tuple[int, int, int],
        tolerance: float = 15.0,
    ) -> bool:
        """Checks if two colors match within tolerance."""
        return cls.color_distance(c1, c2) <= tolerance

    @classmethod
    def check_trigger(
        cls,
        x: int,
        y: int,
        target_color: Tuple[int, int, int],
        condition: str = "MATCH",  # 'MATCH' or 'DIFFER'
        tolerance: float = 15.0,
    ) -> bool:
        """
        Samples (x, y) and evaluates the trigger condition.
        'MATCH': True if screen color matches target_color within tolerance.
        'DIFFER': True if screen color differs from target_color beyond tolerance.
        """
        current_color = cls.get_pixel_color(x, y)
        is_match = cls.matches(current_color, target_color, tolerance)
        if condition == "MATCH":
            return is_match
        else:
            return not is_match
