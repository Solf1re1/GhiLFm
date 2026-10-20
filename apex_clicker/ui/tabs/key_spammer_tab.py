"""
Keyboard Auto-Presser & Key Spammer Tab.
Enables rapid key spamming, cycling skill keys (1-4), or holding keys down continuously
for games, abilities, and repetitive tasks.
"""

import customtkinter as ctk


class KeySpammerTab(ctk.CTkScrollableFrame):
    """Tab for keyboard spamming and multi-key sequences."""

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="kspam_col")

        # --- LEFT CARD: Key Selection & Mode ---
        left_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        left_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        ctk.CTkLabel(
            left_card,
            text="⌨️ Key Target & Execution Mode",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Keys Entry
        ctk.CTkLabel(
            left_card,
            text="Keys to Spam (comma-separated):",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.keys_entry = ctk.CTkEntry(
            left_card,
            placeholder_text="e.g. e or 1, 2, 3, 4 or space",
            height=28,
        )
        self.keys_entry.pack(fill="x", padx=14, pady=(2, 4))
        self.keys_entry.insert(0, "e")
        self.keys_entry.bind("<KeyRelease>", self._on_keys_changed)

        ctk.CTkLabel(
            left_card,
            text="Supports single keys (e, f), numbers (1-9), space, enter, tab.",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # Divider
        ctk.CTkFrame(left_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=4)

        # Mode Selection
        ctk.CTkLabel(
            left_card,
            text="Execution Mode:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.mode_selector = ctk.CTkOptionMenu(
            left_card,
            values=[
                "Simultaneous (Tap together)",
                "Cycle (Sequence in order)",
                "Hold (Keep held down)",
            ],
            command=self._on_mode_changed,
        )
        self.mode_selector.pack(fill="x", padx=14, pady=(2, 8))
        self.mode_selector.set("Simultaneous (Tap together)")

        # Quick preset buttons
        preset_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        preset_frame.pack(fill="x", padx=14, pady=(2, 10))
        preset_frame.grid_columnconfigure((0, 1, 2), weight=1)

        presets = [("E Spam", "e"), ("1-4 Rotation", "1, 2, 3, 4"), ("Space Jump", "space")]
        for idx, (label, val) in enumerate(presets):
            btn = ctk.CTkButton(
                preset_frame,
                text=label,
                width=0,
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#313244",
                hover_color="#45475a",
                command=lambda v=val: self._set_keys_preset(v),
            )
            btn.grid(row=0, column=idx, padx=2, sticky="ew")

        # --- RIGHT CARD: Rate, Jitter & Activation ---
        right_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        right_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        ctk.CTkLabel(
            right_card,
            text="⚡ Speed & Anti-Detection",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Speed / Interval Slider
        speed_header = ctk.CTkFrame(right_card, fg_color="transparent")
        speed_header.pack(fill="x", padx=14, pady=(4, 2))
        ctk.CTkLabel(speed_header, text="Spam Rate:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cdd6f4").pack(side="left")
        self.rate_val_label = ctk.CTkLabel(speed_header, text="10/s (100ms)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.rate_val_label.pack(side="right")

        self.rate_slider = ctk.CTkSlider(
            right_card,
            from_=1,
            to=50,
            number_of_steps=49,
            command=self._on_rate_changed,
        )
        self.rate_slider.pack(fill="x", padx=14, pady=(2, 6))
        self.rate_slider.set(10)

        # Delay Randomization Slider
        rand_header = ctk.CTkFrame(right_card, fg_color="transparent")
        rand_header.pack(fill="x", padx=14, pady=(4, 2))
        ctk.CTkLabel(rand_header, text="Delay Jitter:", font=ctk.CTkFont(size=12), text_color="#a6adc8").pack(side="left")
        self.jitter_val_label = ctk.CTkLabel(rand_header, text="±15%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.jitter_val_label.pack(side="right")

        self.jitter_slider = ctk.CTkSlider(
            right_card,
            from_=0,
            to=50,
            number_of_steps=50,
            command=self._on_jitter_changed,
        )
        self.jitter_slider.pack(fill="x", padx=14, pady=(2, 8))
        self.jitter_slider.set(15)

        # Activate Mode Button
        self.activate_btn = ctk.CTkButton(
            right_card,
            text="✅ Set Active Mode: Keyboard Spammer",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=34,
            command=self._activate_mode,
        )
        self.activate_btn.pack(fill="x", padx=14, pady=(10, 12))

    def _sync_from_config(self):
        cfg = self.engine.keyspam_config
        keys = cfg.get("keys", ["e"])
        self.keys_entry.delete(0, "end")
        self.keys_entry.insert(0, ", ".join(keys))

        intv = cfg.get("interval", 0.1)
        rate = int(round(1.0 / intv)) if intv > 0 else 10
        self.rate_slider.set(min(50, max(1, rate)))
        self.rate_val_label.configure(text=f"{rate} presses/sec ({int(intv*1000)}ms)")

        j_pct = int(cfg.get("jitter_percent", 0.15) * 100)
        self.jitter_slider.set(j_pct)
        self.jitter_val_label.configure(text=f"±{j_pct}%")

    def _on_keys_changed(self, event=None):
        raw = self.keys_entry.get()
        keys = [k.strip().lower() for k in raw.split(",") if k.strip()]
        self.engine.keyspam_config["keys"] = keys or ["e"]

    def _set_keys_preset(self, val: str):
        self.keys_entry.delete(0, "end")
        self.keys_entry.insert(0, val)
        self._on_keys_changed()

    def _on_mode_changed(self, choice: str):
        if "Simultaneous" in choice:
            self.engine.keyspam_config["mode"] = "SIMULTANEOUS"
        elif "Cycle" in choice:
            self.engine.keyspam_config["mode"] = "CYCLE"
        elif "Hold" in choice:
            self.engine.keyspam_config["mode"] = "HOLD"

    def _on_rate_changed(self, val):
        rate = int(round(val))
        intv = 1.0 / max(1, rate)
        self.rate_val_label.configure(text=f"{rate} presses/sec ({int(intv*1000)}ms)")
        self.engine.keyspam_config["interval"] = intv

    def _on_jitter_changed(self, val):
        j = int(round(val))
        self.jitter_val_label.configure(text=f"±{j}%")
        self.engine.keyspam_config["jitter_percent"] = j / 100.0

    def _activate_mode(self):
        self.engine.mode = self.engine.MODE_KEYSPAM
        self.activate_btn.configure(text="🌟 Active Mode is KEY SPAMMER", fg_color="#2b5c3b")
