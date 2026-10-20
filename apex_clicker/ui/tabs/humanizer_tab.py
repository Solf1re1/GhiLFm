"""
Humanizer & Anti-Detection Tab.
Configures realistic human mouse motion, Gaussian coordinate jitter,
randomized delay variances, and fatigue micro-pauses.
"""

import customtkinter as ctk


class HumanizerTab(ctk.CTkScrollableFrame):
    """Tab for anti-cheat and anti-bot human simulation settings."""

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine

        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="human_col")

        # --- LEFT CARD: Movement & Jitter ---
        left_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        left_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        # Master Toggle
        self.master_human_var = ctk.BooleanVar(value=False)
        master_cb = ctk.CTkSwitch(
            left_card,
            text="Anti-Detection Suite",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            variable=self.master_human_var,
            command=self._on_master_toggle,
            progress_color="#a6e3a1",
        )
        master_cb.pack(anchor="w", padx=14, pady=(14, 8))

        # Spatial Jitter (Gaussian dispersion)
        ctk.CTkLabel(
            left_card,
            text="Spatial Coordinate Jitter (Pixels):",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 2))

        jitter_header = ctk.CTkFrame(left_card, fg_color="transparent")
        jitter_header.pack(fill="x", padx=14)
        ctk.CTkLabel(jitter_header, text="Dispersion Radius:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")
        self.jitter_radius_label = ctk.CTkLabel(jitter_header, text="3 px", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.jitter_radius_label.pack(side="right")

        self.jitter_slider = ctk.CTkSlider(
            left_card,
            from_=0,
            to=15,
            number_of_steps=15,
            command=self._on_jitter_slider_changed,
        )
        self.jitter_slider.pack(fill="x", padx=14, pady=(2, 4))
        self.jitter_slider.set(3)

        ctk.CTkLabel(
            left_card,
            text="Simulates natural hand tremors using a 2D Gaussian bell curve.",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # Divider
        ctk.CTkFrame(left_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Smooth Bezier Movement
        ctk.CTkLabel(
            left_card,
            text="Natural Bezier Trajectories:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 2))

        glide_header = ctk.CTkFrame(left_card, fg_color="transparent")
        glide_header.pack(fill="x", padx=14)
        ctk.CTkLabel(glide_header, text="Glide Duration:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")
        self.glide_label = ctk.CTkLabel(glide_header, text="0.25s", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.glide_label.pack(side="right")

        self.glide_slider = ctk.CTkSlider(
            left_card,
            from_=0.05,
            to=0.8,
            number_of_steps=15,
            command=self._on_glide_slider_changed,
        )
        self.glide_slider.pack(fill="x", padx=14, pady=(2, 4))
        self.glide_slider.set(0.25)

        ctk.CTkLabel(
            left_card,
            text="Smooth biological cubic acceleration/deceleration curves.",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # --- RIGHT CARD: Temporal Variance & Fatigue ---
        right_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        right_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        title2 = ctk.CTkLabel(
            right_card,
            text="⏳ Temporal Variance & Fatigue",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        )
        title2.pack(anchor="w", padx=14, pady=(14, 6))

        # Delay Randomization
        del_header = ctk.CTkFrame(right_card, fg_color="transparent")
        del_header.pack(fill="x", padx=14, pady=(4, 2))
        ctk.CTkLabel(del_header, text="Interval Randomization:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cdd6f4").pack(side="left")
        self.delay_pct_label = ctk.CTkLabel(del_header, text="±20%", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.delay_pct_label.pack(side="right")

        self.delay_slider = ctk.CTkSlider(
            right_card,
            from_=0,
            to=50,
            number_of_steps=50,
            command=self._on_delay_slider_changed,
        )
        self.delay_slider.pack(fill="x", padx=14, pady=(2, 4))
        self.delay_slider.set(20)

        ctk.CTkLabel(
            right_card,
            text="Varies click timing per action to break automated detection rhythms.",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # Divider
        ctk.CTkFrame(right_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Fatigue micro-pauses
        self.fatigue_var = ctk.BooleanVar(value=False)
        fatigue_cb = ctk.CTkSwitch(
            right_card,
            text="Simulate Fatigue Micro-Pauses",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            variable=self.fatigue_var,
            command=self._on_fatigue_toggle,
            progress_color="#89b4fa",
        )
        fatigue_cb.pack(anchor="w", padx=14, pady=(8, 4))

        ctk.CTkLabel(
            right_card,
            text="Inserts organic 150-300ms hesitation pauses mimicking human fatigue.",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Anti-detection badge
        status_box = ctk.CTkFrame(right_card, fg_color="#1e1e2e", corner_radius=8)
        status_box.pack(fill="x", padx=14, pady=(6, 12))
        self.anti_detect_status = ctk.CTkLabel(
            status_box,
            text="🛡️ Anti-Detection: ACTIVE",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#a6e3a1",
        )
        self.anti_detect_status.pack(padx=10, pady=8)

    def _sync_from_config(self):
        bcfg = self.engine.burst_config
        active = bcfg.get("humanizer_enabled", False)
        self.master_human_var.set(active)
        self.jitter_slider.set(bcfg.get("jitter_radius", 3))
        self.jitter_radius_label.configure(text=f"{bcfg.get('jitter_radius', 3)} px")
        self.delay_slider.set(int(bcfg.get("jitter_percent", 0.20) * 100))
        self.delay_pct_label.configure(text=f"±{int(bcfg.get('jitter_percent', 0.20) * 100)}%")
        self.fatigue_var.set(bcfg.get("fatigue_enabled", False))
        self._update_status_badge()

    def _update_status_badge(self):
        if self.master_human_var.get():
            self.anti_detect_status.configure(text="🛡️ Anti-Detection: ACTIVE", text_color="#a6e3a1")
        else:
            self.anti_detect_status.configure(text="⚠️ Anti-Detection: DISABLED (Machine Precision)", text_color="#f9e2af")

    def _on_master_toggle(self):
        active = self.master_human_var.get()
        self.engine.burst_config["humanizer_enabled"] = active
        self.engine.sequence_config["humanizer_enabled"] = active
        self._update_status_badge()

    def _on_jitter_slider_changed(self, value):
        rad = int(round(value))
        self.jitter_radius_label.configure(text=f"{rad} px")
        self.engine.burst_config["jitter_radius"] = rad

    def _on_delay_slider_changed(self, value):
        pct = int(round(value))
        self.delay_pct_label.configure(text=f"±{pct}%")
        self.engine.burst_config["jitter_percent"] = pct / 100.0

    def _on_glide_slider_changed(self, value):
        val = round(value, 2)
        self.glide_label.configure(text=f"{val:.2f}s")

    def _on_fatigue_toggle(self):
        self.engine.burst_config["fatigue_enabled"] = self.fatigue_var.get()
