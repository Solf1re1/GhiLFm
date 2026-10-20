"""
Burst / Standard Clicker Tab.
Provides millisecond-precise interval tuning, high-speed CPS slider (up to 1000 CPS),
mouse button selection, fixed vs dynamic cursor targeting, and repeat counters.
"""

import customtkinter as ctk
from typing import Callable, Optional
from apex_clicker.core.input_driver import InputDriver


class BurstTab(ctk.CTkScrollableFrame):
    """Tab for Standard & Extreme Burst auto-clicking configuration."""

    def __init__(self, master, engine, on_pick_request: Optional[Callable[[], None]] = None):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self.on_pick_request = on_pick_request
        self._updating = False

        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        # 2-column layout container
        self.grid_columnconfigure((0, 1), weight=1, uniform="burst_col")

        # --- LEFT CARD: Speed & Interval ---
        speed_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        speed_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        title1 = ctk.CTkLabel(
            speed_card,
            text="⚡ Speed & Interval Tuning",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        )
        title1.pack(anchor="w", padx=14, pady=(12, 6))

        # CPS Slider section
        cps_header_frame = ctk.CTkFrame(speed_card, fg_color="transparent")
        cps_header_frame.pack(fill="x", padx=14, pady=(4, 0))

        ctk.CTkLabel(
            cps_header_frame,
            text="Clicks Per Second (CPS):",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a6adc8",
        ).pack(side="left")

        self.cps_val_label = ctk.CTkLabel(
            cps_header_frame,
            text="100 CPS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#89b4fa",
        )
        self.cps_val_label.pack(side="right")

        self.cps_slider = ctk.CTkSlider(
            speed_card,
            from_=1,
            to=500,
            number_of_steps=499,
            command=self._on_cps_slider_changed,
        )
        self.cps_slider.pack(fill="x", padx=14, pady=(4, 10))
        self.cps_slider.set(100)

        # Quick preset buttons (10 CPS, 25 CPS, 50 CPS, 100 CPS, 500 CPS)
        preset_frame = ctk.CTkFrame(speed_card, fg_color="transparent")
        preset_frame.pack(fill="x", padx=14, pady=(0, 12))
        preset_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        cps_presets = [("10", 10), ("25", 25), ("50", 50), ("100", 100), ("500", 500)]
        for idx, (label, val) in enumerate(cps_presets):
            btn = ctk.CTkButton(
                preset_frame,
                text=label,
                width=0,
                height=26,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#313244",
                hover_color="#45475a",
                command=lambda v=val: self.set_cps(v),
            )
            btn.grid(row=0, column=idx, padx=2, sticky="ew")

        # Divider
        ctk.CTkFrame(speed_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Milliseconds / Seconds precise inputs
        ctk.CTkLabel(
            speed_card,
            text="Custom Interval (Manual):",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 4))

        int_row = ctk.CTkFrame(speed_card, fg_color="transparent")
        int_row.pack(fill="x", padx=14, pady=4)
        int_row.grid_columnconfigure((0, 1), weight=1)

        # Sec
        sec_box = ctk.CTkFrame(int_row, fg_color="transparent")
        sec_box.grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkLabel(sec_box, text="Seconds", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w")
        self.sec_entry = ctk.CTkEntry(sec_box, height=28, justify="center")
        self.sec_entry.insert(0, "0")
        self.sec_entry.pack(fill="x", pady=(2, 0))
        self.sec_entry.bind("<KeyRelease>", self._on_manual_interval_changed)

        # Millisec
        ms_box = ctk.CTkFrame(int_row, fg_color="transparent")
        ms_box.grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkLabel(ms_box, text="Milliseconds", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w")
        self.ms_entry = ctk.CTkEntry(ms_box, height=28, justify="center")
        self.ms_entry.insert(0, "10")
        self.ms_entry.pack(fill="x", pady=(2, 0))
        self.ms_entry.bind("<KeyRelease>", self._on_manual_interval_changed)

        # Repeat limits
        ctk.CTkLabel(
            speed_card,
            text="Repeat Limit:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 4))

        self.repeat_mode_var = ctk.StringVar(value="infinite")
        r_inf = ctk.CTkRadioButton(
            speed_card,
            text="Repeat continuously until stopped",
            variable=self.repeat_mode_var,
            value="infinite",
            font=ctk.CTkFont(size=11),
            command=self._on_repeat_mode_changed,
        )
        r_inf.pack(anchor="w", padx=14, pady=2)

        r_count_frame = ctk.CTkFrame(speed_card, fg_color="transparent")
        r_count_frame.pack(fill="x", padx=14, pady=(2, 12))
        r_limit = ctk.CTkRadioButton(
            r_count_frame,
            text="Stop after",
            variable=self.repeat_mode_var,
            value="count",
            font=ctk.CTkFont(size=11),
            command=self._on_repeat_mode_changed,
        )
        r_limit.pack(side="left")

        self.repeat_count_entry = ctk.CTkEntry(r_count_frame, width=70, height=26, justify="center")
        self.repeat_count_entry.insert(0, "100")
        self.repeat_count_entry.pack(side="left", padx=8)
        self.repeat_count_entry.bind("<KeyRelease>", self._on_repeat_count_changed)
        ctk.CTkLabel(r_count_frame, text="clicks", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")

        # --- RIGHT CARD: Target & Mouse Button ---
        target_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        target_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        title2 = ctk.CTkLabel(
            target_card,
            text="🎯 Mouse Action & Target",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        )
        title2.pack(anchor="w", padx=14, pady=(12, 6))

        # Button type
        ctk.CTkLabel(
            target_card,
            text="Mouse Button / Action:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a6adc8",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.button_selector = ctk.CTkOptionMenu(
            target_card,
            values=[
                "Left Click",
                "Right Click",
                "Middle Click",
                "Double Click",
                "Triple Click",
                "Scroll Up",
                "Scroll Down",
                "Hold Left",
            ],
            command=self._on_button_changed,
        )
        self.button_selector.pack(fill="x", padx=14, pady=(2, 10))
        self.button_selector.set("Left Click")

        # Divider
        ctk.CTkFrame(target_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Target Location
        ctk.CTkLabel(
            target_card,
            text="Target Coordinate:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 4))

        self.target_mode_var = ctk.StringVar(value="CURRENT")
        t_curr = ctk.CTkRadioButton(
            target_card,
            text="Follow Current Mouse Cursor",
            variable=self.target_mode_var,
            value="CURRENT",
            font=ctk.CTkFont(size=11),
            command=self._on_target_mode_changed,
        )
        t_curr.pack(anchor="w", padx=14, pady=2)

        t_fix = ctk.CTkRadioButton(
            target_card,
            text="Fixed Screen Coordinate",
            variable=self.target_mode_var,
            value="FIXED",
            font=ctk.CTkFont(size=11),
            command=self._on_target_mode_changed,
        )
        t_fix.pack(anchor="w", padx=14, pady=2)

        # Coordinate inputs
        coord_row = ctk.CTkFrame(target_card, fg_color="transparent")
        coord_row.pack(fill="x", padx=14, pady=(4, 8))

        ctk.CTkLabel(coord_row, text="X:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")
        self.x_entry = ctk.CTkEntry(coord_row, width=65, height=26, justify="center")
        self.x_entry.insert(0, "0")
        self.x_entry.pack(side="left", padx=(4, 12))
        self.x_entry.bind("<KeyRelease>", self._on_coord_changed)

        ctk.CTkLabel(coord_row, text="Y:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")
        self.y_entry = ctk.CTkEntry(coord_row, width=65, height=26, justify="center")
        self.y_entry.insert(0, "0")
        self.y_entry.pack(side="left", padx=4)
        self.y_entry.bind("<KeyRelease>", self._on_coord_changed)

        # Pick coordinate button
        self.pick_btn = ctk.CTkButton(
            target_card,
            text="📍 Pick Coordinate [Ctrl+F8]",
            fg_color="#313244",
            hover_color="#45475a",
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._trigger_pick_location,
        )
        self.pick_btn.pack(fill="x", padx=14, pady=(4, 10))

        # Tip box
        tip_box = ctk.CTkFrame(target_card, fg_color="#1e1e2e", corner_radius=8)
        tip_box.pack(fill="x", padx=14, pady=(6, 12))
        ctk.CTkLabel(
            tip_box,
            text="💡 Tip: Press Ctrl+F8 anywhere on your screen at\nany time to capture the cursor position!",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#89b4fa",
            justify="left",
        ).pack(padx=10, pady=8)

    def _sync_from_config(self):
        cfg = self.engine.burst_config
        self.target_mode_var.set(cfg.get("target_mode", "CURRENT"))
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(cfg.get("fixed_x", 0)))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(cfg.get("fixed_y", 0)))

        interval = cfg.get("interval", 0.01)
        cps = 1.0 / interval if interval > 0 else 100
        self.set_cps(min(500, max(1, int(round(cps)))), sync_entry=True)

    def set_cps(self, cps: int, sync_entry: bool = True):
        self._updating = True
        try:
            self.cps_slider.set(cps)
            self.cps_val_label.configure(text=f"{cps} CPS")
            interval = 1.0 / max(1, cps)
            self.engine.burst_config["interval"] = interval

            if sync_entry:
                ms = int(interval * 1000)
                sec = int(interval)
                rem_ms = int((interval - sec) * 1000)
                self.sec_entry.delete(0, "end")
                self.sec_entry.insert(0, str(sec))
                self.ms_entry.delete(0, "end")
                self.ms_entry.insert(0, str(rem_ms if sec > 0 else ms))
        finally:
            self._updating = False

    def _on_cps_slider_changed(self, value):
        if self._updating:
            return
        cps = int(round(value))
        self.set_cps(cps, sync_entry=True)

    def _on_manual_interval_changed(self, event=None):
        if self._updating:
            return
        try:
            sec = float(self.sec_entry.get().strip() or "0")
            ms = float(self.ms_entry.get().strip() or "0")
            total_sec = max(0.001, sec + (ms / 1000.0))
            self.engine.burst_config["interval"] = total_sec
            cps = int(round(1.0 / total_sec))
            self.cps_val_label.configure(text=f"{cps} CPS")
            self._updating = True
            self.cps_slider.set(min(500, max(1, cps)))
            self._updating = False
        except ValueError:
            pass

    def _on_button_changed(self, choice: str):
        mapping = {
            "Left Click": "left",
            "Right Click": "right",
            "Middle Click": "middle",
            "Double Click": "double",
            "Triple Click": "triple",
            "Scroll Up": "scroll_up",
            "Scroll Down": "scroll_down",
            "Hold Left": "hold_left",
        }
        self.engine.burst_config["button"] = mapping.get(choice, "left")

    def _on_target_mode_changed(self):
        self.engine.burst_config["target_mode"] = self.target_mode_var.get()

    def _on_coord_changed(self, event=None):
        try:
            x = int(self.x_entry.get().strip() or "0")
            y = int(self.y_entry.get().strip() or "0")
            self.engine.burst_config["fixed_x"] = x
            self.engine.burst_config["fixed_y"] = y
        except ValueError:
            pass

    def _on_repeat_mode_changed(self):
        if self.repeat_mode_var.get() == "infinite":
            self.engine.burst_config["repeat_limit"] = 0
        else:
            self._on_repeat_count_changed()

    def _on_repeat_count_changed(self, event=None):
        if self.repeat_mode_var.get() == "count":
            try:
                count = int(self.repeat_count_entry.get().strip() or "1")
                self.engine.burst_config["repeat_limit"] = max(1, count)
            except ValueError:
                self.engine.burst_config["repeat_limit"] = 100

    def set_coordinate(self, x: int, y: int):
        """Sets fixed coordinate from external picker/hotkey."""
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(x))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(y))
        self.target_mode_var.set("FIXED")
        self._on_coord_changed()
        self._on_target_mode_changed()

    def _trigger_pick_location(self):
        if self.on_pick_request:
            self.on_pick_request()
        else:
            x, y = InputDriver.get_cursor_pos()
            self.set_coordinate(x, y)
