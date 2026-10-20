"""
Pixel & Color Trigger Tab.
Enables reactive clicking triggered by screen color matches or state changes
with real-time eyedropper sampling and color preview.
"""

import customtkinter as ctk
from apex_clicker.core.input_driver import InputDriver
from apex_clicker.core.pixel_detector import PixelDetector


class PixelTab(ctk.CTkScrollableFrame):
    """Tab for screen pixel color monitoring and reactive triggers."""

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="pixel_col")

        # --- LEFT CARD: Coordinate & Color Sampling ---
        left_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        left_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        ctk.CTkLabel(
            left_card,
            text="👁️ Target Pixel & Sampling",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Sample Button
        self.sample_btn = ctk.CTkButton(
            left_card,
            text="🎯 Sample Cursor Pixel [Ctrl+F9]",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            height=32,
            command=self.sample_current_cursor,
        )
        self.sample_btn.pack(fill="x", padx=14, pady=(4, 8))

        # Coordinate Row
        coord_row = ctk.CTkFrame(left_card, fg_color="transparent")
        coord_row.pack(fill="x", padx=14, pady=4)

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

        # Color Swatch & Details
        color_frame = ctk.CTkFrame(left_card, fg_color="#1e1e2e", corner_radius=8)
        color_frame.pack(fill="x", padx=14, pady=(8, 8))

        self.color_swatch = ctk.CTkFrame(color_frame, width=40, height=40, corner_radius=6, fg_color="#FF0000")
        self.color_swatch.pack(side="left", padx=10, pady=8)
        self.color_swatch.pack_propagate(False)

        info_box = ctk.CTkFrame(color_frame, fg_color="transparent")
        info_box.pack(side="left", padx=4, pady=4)

        self.hex_label = ctk.CTkLabel(
            info_box,
            text="#FF0000",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#cdd6f4",
        )
        self.hex_label.pack(anchor="w")

        self.rgb_label = ctk.CTkLabel(
            info_box,
            text="RGB(255, 0, 0)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#a6adc8",
        )
        self.rgb_label.pack(anchor="w")

        # Tolerance Slider
        ctk.CTkLabel(
            left_card,
            text="Color Match Tolerance:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 2))

        tol_header = ctk.CTkFrame(left_card, fg_color="transparent")
        tol_header.pack(fill="x", padx=14)
        ctk.CTkLabel(tol_header, text="Tolerance:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")
        self.tol_val_label = ctk.CTkLabel(tol_header, text="15", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.tol_val_label.pack(side="right")

        self.tol_slider = ctk.CTkSlider(
            left_card,
            from_=0,
            to=80,
            number_of_steps=80,
            command=self._on_tolerance_changed,
        )
        self.tol_slider.pack(fill="x", padx=14, pady=(2, 12))
        self.tol_slider.set(15)

        # --- RIGHT CARD: Trigger Logic & Action ---
        right_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        right_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        ctk.CTkLabel(
            right_card,
            text="⚙️ Trigger Logic & Action",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Condition
        ctk.CTkLabel(
            right_card,
            text="Condition:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.cond_selector = ctk.CTkOptionMenu(
            right_card,
            values=["Color MATCHES Target", "Color DIFFERS from Target"],
            command=self._on_condition_changed,
        )
        self.cond_selector.pack(fill="x", padx=14, pady=(2, 8))
        self.cond_selector.set("Color MATCHES Target")

        # Action
        ctk.CTkLabel(
            right_card,
            text="Action on Trigger:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.action_selector = ctk.CTkOptionMenu(
            right_card,
            values=["Click Repeatedly While Triggered", "Click Once (with cooldown)"],
            command=self._on_action_changed,
        )
        self.action_selector.pack(fill="x", padx=14, pady=(2, 8))
        self.action_selector.set("Click Repeatedly While Triggered")

        # Button type
        ctk.CTkLabel(
            right_card,
            text="Mouse Click:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a6adc8",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.btn_selector = ctk.CTkOptionMenu(
            right_card,
            values=["left", "right", "double"],
            command=self._on_btn_changed,
        )
        self.btn_selector.pack(fill="x", padx=14, pady=(2, 10))
        self.btn_selector.set("left")

        # Activate Mode Button
        self.activate_mode_btn = ctk.CTkButton(
            right_card,
            text="✅ Set Active Mode: Pixel Trigger",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=34,
            command=self._activate_pixel_mode,
        )
        self.activate_mode_btn.pack(fill="x", padx=14, pady=(8, 12))

    def _sync_from_config(self):
        cfg = self.engine.pixel_config
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(cfg.get("x", 0)))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(cfg.get("y", 0)))

        color = cfg.get("target_color", (255, 0, 0))
        self.update_color_display(color[0], color[1], color[2])

        tol = int(cfg.get("tolerance", 15.0))
        self.tol_slider.set(tol)
        self.tol_val_label.configure(text=str(tol))

    def update_color_display(self, r: int, g: int, b: int):
        hex_color = PixelDetector.color_to_hex(r, g, b)
        self.color_swatch.configure(fg_color=hex_color)
        self.hex_label.configure(text=hex_color)
        self.rgb_label.configure(text=f"RGB({r}, {g}, {b})")
        self.engine.pixel_config["target_color"] = (r, g, b)

    def sample_current_cursor(self):
        """Samples the pixel coordinate and color currently under the mouse."""
        x, y = InputDriver.get_cursor_pos()
        r, g, b = PixelDetector.get_pixel_color(x, y)
        self.x_entry.delete(0, "end")
        self.x_entry.insert(0, str(x))
        self.y_entry.delete(0, "end")
        self.y_entry.insert(0, str(y))
        self.engine.pixel_config["x"] = x
        self.engine.pixel_config["y"] = y
        self.update_color_display(r, g, b)

    def _on_coord_changed(self, event=None):
        try:
            x = int(self.x_entry.get().strip() or "0")
            y = int(self.y_entry.get().strip() or "0")
            self.engine.pixel_config["x"] = x
            self.engine.pixel_config["y"] = y
        except ValueError:
            pass

    def _on_tolerance_changed(self, val):
        t = int(round(val))
        self.tol_val_label.configure(text=str(t))
        self.engine.pixel_config["tolerance"] = float(t)

    def _on_condition_changed(self, choice: str):
        cond = "MATCH" if "MATCHES" in choice else "DIFFER"
        self.engine.pixel_config["condition"] = cond

    def _on_action_changed(self, choice: str):
        act = "CLICK_WHILE" if "While" in choice else "CLICK_ONCE"
        self.engine.pixel_config["action"] = act

    def _on_btn_changed(self, choice: str):
        self.engine.pixel_config["button"] = choice.lower()

    def _activate_pixel_mode(self):
        self.engine.mode = self.engine.MODE_PIXEL
        self.activate_mode_btn.configure(text="🌟 Active Mode is PIXEL TRIGGER", fg_color="#2b5c3b")
