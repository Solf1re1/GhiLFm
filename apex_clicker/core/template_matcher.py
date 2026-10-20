"""
Template / Image Search Engine.
Locates UI buttons, icons, or visual game elements on screen using OpenCV template matching
and calculates accurate center click coordinates.
"""

import os
from typing import Optional, Tuple, List, Any
import cv2
import numpy as np
import mss
from PIL import ImageGrab
from apex_clicker.core.input_driver import InputDriver


class TemplateMatcher:
    """Fast screen template matching via mss and OpenCV."""

    _sct = None

    @classmethod
    def _get_sct(cls):
        if cls._sct is None:
            cls._sct = mss.mss()
        return cls._sct

    @classmethod
    def capture_fullscreen_bgr(cls, monitor_idx: int = 0) -> Tuple[np.ndarray, int, int]:
        """
        Captures monitor as an OpenCV BGR image.
        monitor_idx=0 captures ALL monitors combined across the entire virtual desktop.
        Returns (frame, offset_x, offset_y).
        """
        InputDriver.ensure_desktop_access()
        sct = cls._get_sct()
        try:
            idx = min(max(0, monitor_idx), len(sct.monitors) - 1)
            monitor = sct.monitors[idx]
            screenshot = sct.grab(monitor)
            frame = np.array(screenshot)
            bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return bgr, int(monitor.get("left", 0)), int(monitor.get("top", 0))
        except Exception:
            # Fallback to PIL ImageGrab if MSS encounters GDI BitBlt access restriction
            try:
                if monitor_idx == 0:
                    pil_img = ImageGrab.grab(all_screens=True)
                    u = InputDriver._user32
                    mx = u.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
                    my = u.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
                else:
                    idx = min(max(0, monitor_idx), len(sct.monitors) - 1)
                    monitor = sct.monitors[idx]
                    mx, my = int(monitor.get("left", 0)), int(monitor.get("top", 0))
                    mw, mh = int(monitor.get("width", 1920)), int(monitor.get("height", 1080))
                    pil_img = ImageGrab.grab(bbox=(mx, my, mx + mw, my + mh), all_screens=True)
                frame = np.array(pil_img)
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return bgr, mx, my
            except Exception:
                cls._sct = mss.mss()
                idx = min(max(0, monitor_idx), len(cls._sct.monitors) - 1)
                monitor = cls._sct.monitors[idx]
                screenshot = cls._sct.grab(monitor)
                frame = np.array(screenshot)
                bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                return bgr, int(monitor.get("left", 0)), int(monitor.get("top", 0))

    @classmethod
    def find_template(
        cls,
        template_img: np.ndarray,
        confidence: float = 0.80,
        exclude_rect: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[int, int, float]]:
        """
        Searches all active monitors for template_img.
        Returns (center_x, center_y, confidence) in desktop coordinates, else None.
        """
        if template_img is None or template_img.size == 0:
            return None

        match = cls.find_any_template(
            [(template_img, confidence, None)],
            exclude_rect=exclude_rect,
        )
        if match:
            cx, cy, score, _ = match
            return (cx, cy, score)
        return None

    @classmethod
    def find_any_template(
        cls,
        templates: List[Tuple[np.ndarray, float, Any]],
        screen_bgr: Optional[np.ndarray] = None,
        screen_offset: Tuple[int, int] = (0, 0),
        exclude_rect: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[Tuple[int, int, float, Any]]:
        """
        Searches screen for ANY of the given templates across all monitors:
        templates: list of (template_img_ndarray, confidence_float, metadata_or_id)
        exclude_rect: (x, y, w, h) of window to mask out (e.g. ApexClicker UI)
        Returns (center_x, center_y, confidence, metadata) for the best match found, or None.
        """
        if not templates:
            return None

        best_match = None
        best_score = -1.0

        # If a pre-captured screen is provided, search that single frame
        if screen_bgr is not None:
            screens = [(screen_bgr, screen_offset[0], screen_offset[1])]
        else:
            # Multi-monitor support: capture entire virtual desktop in one pass
            screens = []
            try:
                bgr, off_x, off_y = cls.capture_fullscreen_bgr(0)
                screens.append((bgr, off_x, off_y))
            except Exception:
                # Fallback to per-monitor capture
                sct = cls._get_sct()
                num_monitors = max(1, len(sct.monitors) - 1)
                for m_idx in range(1, num_monitors + 1):
                    try:
                        bgr, off_x, off_y = cls.capture_fullscreen_bgr(m_idx)
                        screens.append((bgr, off_x, off_y))
                    except Exception:
                        pass

        for screen, off_x, off_y in screens:
            if screen is None or screen.size == 0:
                continue

            sh, sw = screen.shape[:2]

            # Mask out exclude_rect (e.g. ApexClicker UI window) to prevent self-matching
            if exclude_rect:
                ex, ey, ew, eh = exclude_rect
                rx1 = max(0, ex - off_x)
                ry1 = max(0, ey - off_y)
                rx2 = min(sw, ex + ew - off_x)
                ry2 = min(sh, ey + eh - off_y)
                if rx2 > rx1 and ry2 > ry1:
                    screen[ry1:ry2, rx1:rx2] = 0

            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            for tpl_img, conf, meta in templates:
                if tpl_img is None or tpl_img.size == 0:
                    continue

                if len(tpl_img.shape) == 3:
                    tpl_gray = cv2.cvtColor(tpl_img, cv2.COLOR_BGR2GRAY)
                else:
                    tpl_gray = tpl_img

                th, tw = tpl_gray.shape[:2]
                if tw > sw or th > sh:
                    continue

                # Robust matching: If template has low variance (flat buttons), CCOEFF divides by 0
                # and falsely matches (0, 0). SQDIFF_NORMED avoids this perfectly.
                tpl_std = float(np.std(tpl_gray))
                if tpl_std < 2.5:
                    res = cv2.matchTemplate(screen_gray, tpl_gray, cv2.TM_SQDIFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    score = float(max(0.0, min(1.0, 1.0 - min_val)))
                    loc = min_loc
                else:
                    res = cv2.matchTemplate(screen_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    score = float(max_val) if not np.isnan(max_val) else 0.0
                    loc = max_loc

                    # Edge-enhanced fallback: If grayscale match is below threshold (e.g. glowing text,
                    # transparency, hover highlight, or dynamic background), evaluate structural edge contours.
                    if score < conf:
                        try:
                            tpl_edge = cv2.Canny(tpl_gray, 50, 150)
                            if np.count_nonzero(tpl_edge) > 15:
                                screen_edge = cv2.Canny(screen_gray, 50, 150)
                                res_e = cv2.matchTemplate(screen_edge, tpl_edge, cv2.TM_CCOEFF_NORMED)
                                _, max_e, _, loc_e = cv2.minMaxLoc(res_e)
                                if not np.isnan(max_e) and float(max_e) > score:
                                    score = float(max_e)
                                    loc = loc_e
                        except Exception:
                            pass

                if score >= conf:
                    if score > best_score:
                        best_score = score
                        cx = off_x + loc[0] + tw // 2
                        cy = off_y + loc[1] + th // 2
                        best_match = (int(cx), int(cy), float(score), meta)

        return best_match

    @classmethod
    def load_template_file(cls, file_path: str) -> Optional[np.ndarray]:
        """Loads template image from disk."""
        if not os.path.exists(file_path):
            return None
        return cv2.imread(file_path, cv2.IMREAD_COLOR)

    @classmethod
    def save_template_crop(cls, file_path: str, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Crops a screen region and saves it as a template."""
        screen, _, _ = cls.capture_fullscreen_bgr()
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        crop = screen[min_y:max_y, min_x:max_x]
        if crop.size == 0:
            return False
        return cv2.imwrite(file_path, crop)
