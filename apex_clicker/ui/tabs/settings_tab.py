"""
Settings & Profiles Tab.
Configures system hotkeys, hold-to-click vs toggle mode, window/game process locking,
animated click ripples, scheduled countdown timers with auto-shutdown, and profile presets.
"""

import customtkinter as ctk
from typing import Callable, Optional
from apex_clicker.core.profile_manager import ProfileManager
from apex_clicker.core.window_lock import WindowLockManager


class SettingsTab(ctk.CTkScrollableFrame):
    """Tab for application settings, global hotkeys, window binding, and scheduler."""

    def __init__(
        self,
        master,
        engine,
        hotkey_mgr,
        on_toggle_hud: Optional[Callable[[bool], None]] = None,
        on_toggle_topmost: Optional[Callable[[bool], None]] = None,
        on_profile_loaded: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self.hotkey_mgr = hotkey_mgr
        self.on_toggle_hud = on_toggle_hud
        self.on_toggle_topmost = on_toggle_topmost
        self.on_profile_loaded = on_profile_loaded

        self._build_ui()
        self._refresh_profiles_list()
        self._refresh_windows_list()
        self._poll_timer_status()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="set_col")

        # --- LEFT CARD: Hotkeys, Window Lock & Behavior ---
        left_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        left_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        ctk.CTkLabel(
            left_card,
            text="⌨️ Global Hotkeys",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Hotkey rows
        hotkey_configs = [
            ("Start / Stop:", "toggle", "ctrl+f6"),
            ("Pause / Resume:", "pause", "ctrl+f7"),
            ("Capture Cursor:", "pick_coord", "ctrl+f8"),
            ("Sample Pixel:", "sample_pixel", "ctrl+f9"),
            ("Record Macro:", "macro_toggle", "ctrl+f10"),
        ]

        self.hotkey_entries = {}
        for label_text, action_id, default_val in hotkey_configs:
            row = ctk.CTkFrame(left_card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left")

            entry = ctk.CTkEntry(row, width=80, height=26, justify="center")
            entry.insert(0, self.hotkey_mgr.get_hotkey_display(action_id) or default_val.upper())
            entry.pack(side="right")
            entry.bind("<KeyRelease>", lambda e, act=action_id, ent=entry: self._on_hotkey_changed(act, ent))
            self.hotkey_entries[action_id] = entry

        # Hotkey Trigger Mode (Toggle vs Hold)
        ctk.CTkLabel(
            left_card,
            text="Hotkey Activation Mode:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(8, 2))

        self.trigger_mode_seg = ctk.CTkSegmentedButton(
            left_card,
            values=["Toggle Mode", "Hold-to-Click"],
            command=self._on_trigger_mode_changed,
        )
        self.trigger_mode_seg.pack(fill="x", padx=14, pady=(2, 6))
        self.trigger_mode_seg.set("Toggle Mode")

        # Divider
        ctk.CTkFrame(left_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Target Window / Game Lock
        ctk.CTkLabel(
            left_card,
            text="🎯 Window / Game Process Lock",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 4))

        win_row = ctk.CTkFrame(left_card, fg_color="transparent")
        win_row.pack(fill="x", padx=14, pady=2)

        self.win_dropdown = ctk.CTkOptionMenu(
            win_row,
            values=["Any Active Window (Unrestricted)"],
            command=self._on_window_selected,
        )
        self.win_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 4))

        refresh_win_btn = ctk.CTkButton(
            win_row,
            text="🔄",
            width=32,
            height=28,
            fg_color="#313244",
            hover_color="#45475a",
            command=self._refresh_windows_list,
        )
        refresh_win_btn.pack(side="right")

        pick_win_btn = ctk.CTkButton(
            left_card,
            text="🎯 Pick Current Foreground Window",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            fg_color="#313244",
            hover_color="#45475a",
            command=self._pick_current_window,
        )
        pick_win_btn.pack(fill="x", padx=14, pady=(4, 4))

        self.lock_status_label = ctk.CTkLabel(
            left_card,
            text="Lock: Inactive (Clicks work in any window)",
            font=ctk.CTkFont(size=11),
            text_color="#89b4fa",
        )
        self.lock_status_label.pack(anchor="w", padx=14, pady=(0, 6))

        # Divider
        ctk.CTkFrame(left_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # General Preferences
        ctk.CTkLabel(
            left_card,
            text="⚙️ Preferences & Visuals",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 4))

        self.sound_var = ctk.BooleanVar(value=self.engine.sound_enabled)
        sound_cb = ctk.CTkSwitch(
            left_card,
            text="Audible Audio Cues (Start/Stop Beeps)",
            font=ctk.CTkFont(size=11),
            variable=self.sound_var,
            command=self._on_sound_toggle,
            progress_color="#89b4fa",
        )
        sound_cb.pack(anchor="w", padx=14, pady=2)

        self.topmost_var = ctk.BooleanVar(value=True)
        topmost_cb = ctk.CTkSwitch(
            left_card,
            text="Pin Window Always On Top",
            font=ctk.CTkFont(size=11),
            variable=self.topmost_var,
            command=self._on_topmost_toggle,
            progress_color="#89b4fa",
        )
        topmost_cb.pack(anchor="w", padx=14, pady=2)

        self.hud_var = ctk.BooleanVar(value=False)
        hud_cb = ctk.CTkSwitch(
            left_card,
            text="Display Floating Mini-HUD Overlay",
            font=ctk.CTkFont(size=11),
            variable=self.hud_var,
            command=self._on_hud_toggle,
            progress_color="#a6e3a1",
        )
        hud_cb.pack(anchor="w", padx=14, pady=2)

        self.shortcut_btn = ctk.CTkButton(
            left_card,
            text="🔗 Create Desktop Shortcut",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            height=28,
            command=self._create_desktop_shortcut,
        )
        self.shortcut_btn.pack(fill="x", padx=14, pady=(6, 2))

        self.shortcut_status_label = ctk.CTkLabel(
            left_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#a6e3a1",
        )
        self.shortcut_status_label.pack(anchor="w", padx=14, pady=(0, 8))

        # Divider
        ctk.CTkFrame(left_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # About & GitHub Updates
        ctk.CTkLabel(
            left_card,
            text="ℹ️ About & Updates",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 4))

        about_row = ctk.CTkFrame(left_card, fg_color="transparent")
        about_row.pack(fill="x", padx=14, pady=(2, 4))

        from apex_clicker import __version__
        ctk.CTkLabel(
            about_row,
            text=f"ApexClicker Pro v{__version__}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#89b4fa",
        ).pack(side="left")

        ctk.CTkLabel(
            about_row,
            text="• Official Release",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
        ).pack(side="left", padx=(6, 0))

        check_update_btn = ctk.CTkButton(
            left_card,
            text="🌐 Check for Updates on GitHub",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            height=30,
            command=self._check_for_updates,
        )
        check_update_btn.pack(fill="x", padx=14, pady=(2, 2))

        gh_url_lbl = ctk.CTkLabel(
            left_card,
            text="https://github.com/Solf1re1/GhiLFm",
            font=ctk.CTkFont(size=10),
            text_color="#6c7086",
        )
        gh_url_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        # --- RIGHT CARD: Scheduler & Profiles ---
        right_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        right_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        # Scheduled Timer Section
        ctk.CTkLabel(
            right_card,
            text="⏱️ Scheduled Timer & Auto-Shutdown",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.sched_var = ctk.BooleanVar(value=False)
        sched_cb = ctk.CTkSwitch(
            right_card,
            text="Enable Auto-Stop Duration Limit",
            font=ctk.CTkFont(size=11),
            variable=self.sched_var,
            command=self._on_sched_toggle,
            progress_color="#89b4fa",
        )
        sched_cb.pack(anchor="w", padx=14, pady=(2, 6))

        # Timer Inputs (Hours, Mins, Secs)
        time_row = ctk.CTkFrame(right_card, fg_color="transparent")
        time_row.pack(fill="x", padx=14, pady=4)
        time_row.grid_columnconfigure((0, 1, 2), weight=1)

        h_box = ctk.CTkFrame(time_row, fg_color="transparent")
        h_box.grid(row=0, column=0, padx=2)
        ctk.CTkLabel(h_box, text="Hours", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack()
        self.sched_h = ctk.CTkEntry(h_box, width=50, height=26, justify="center")
        self.sched_h.insert(0, "0")
        self.sched_h.pack()
        self.sched_h.bind("<KeyRelease>", self._on_sched_time_changed)

        m_box = ctk.CTkFrame(time_row, fg_color="transparent")
        m_box.grid(row=0, column=1, padx=2)
        ctk.CTkLabel(m_box, text="Minutes", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack()
        self.sched_m = ctk.CTkEntry(m_box, width=50, height=26, justify="center")
        self.sched_m.insert(0, "30")
        self.sched_m.pack()
        self.sched_m.bind("<KeyRelease>", self._on_sched_time_changed)

        s_box = ctk.CTkFrame(time_row, fg_color="transparent")
        s_box.grid(row=0, column=2, padx=2)
        ctk.CTkLabel(s_box, text="Seconds", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack()
        self.sched_s = ctk.CTkEntry(s_box, width=50, height=26, justify="center")
        self.sched_s.insert(0, "0")
        self.sched_s.pack()
        self.sched_s.bind("<KeyRelease>", self._on_sched_time_changed)

        # Action on completion
        ctk.CTkLabel(
            right_card,
            text="Action on Timer Completion:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(6, 2))

        self.sched_action_selector = ctk.CTkOptionMenu(
            right_card,
            values=[
                "Stop Auto Clicker Only",
                "Play Audible Alarm Beep",
                "Put PC to Sleep (Suspend)",
                "Shut Down Computer",
            ],
            command=self._on_sched_action_changed,
        )
        self.sched_action_selector.pack(fill="x", padx=14, pady=(2, 6))

        self.timer_countdown_label = ctk.CTkLabel(
            right_card,
            text="Countdown: Disabled",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#a6adc8",
        )
        self.timer_countdown_label.pack(anchor="w", padx=14, pady=(2, 8))

        # Divider
        ctk.CTkFrame(right_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Profile & Preset Manager
        ctk.CTkLabel(
            right_card,
            text="📁 Profile & Preset Manager",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 4))

        ctk.CTkLabel(right_card, text="Select Preset / Saved Profile:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w", padx=14, pady=(2, 2))

        self.preset_dropdown = ctk.CTkOptionMenu(right_card, values=["Default"])
        self.preset_dropdown.pack(fill="x", padx=14, pady=2)

        load_btn = ctk.CTkButton(
            right_card,
            text="📥 Load Selected Profile",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            height=28,
            command=self._load_selected_profile,
        )
        load_btn.pack(fill="x", padx=14, pady=(4, 8))

        ctk.CTkLabel(right_card, text="Save Current Settings as Profile:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w", padx=14, pady=(2, 2))

        self.profile_name_entry = ctk.CTkEntry(right_card, placeholder_text="Profile name (e.g. MyGame)", height=28)
        self.profile_name_entry.pack(fill="x", padx=14, pady=2)

        save_btn = ctk.CTkButton(
            right_card,
            text="💾 Save Profile",
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            command=self._save_current_profile,
        )
        save_btn.pack(fill="x", padx=14, pady=(4, 6))

        self.save_status_label = ctk.CTkLabel(right_card, text="", font=ctk.CTkFont(size=11), text_color="#a6e3a1")
        self.save_status_label.pack(anchor="w", padx=14, pady=(0, 8))

    def _refresh_profiles_list(self):
        profiles = ProfileManager.list_profiles()
        if profiles:
            self.preset_dropdown.configure(values=profiles)
            self.preset_dropdown.set(profiles[0])

    def _refresh_windows_list(self):
        wins = WindowLockManager.list_visible_windows()
        labels = ["Any Active Window (Unrestricted)"]
        self.window_map = {"Any Active Window (Unrestricted)": ""}
        for label, identifier in wins:
            labels.append(label)
            self.window_map[label] = identifier

        self.win_dropdown.configure(values=labels)
        if not self.engine.target_window:
            self.win_dropdown.set(labels[0])

    def _pick_current_window(self):
        fg = WindowLockManager.get_foreground_info()
        pname = fg.get("process", "")
        title = fg.get("title", "")
        if pname:
            self.engine.target_window = pname
            self.win_dropdown.set(f"{title[:40]} ({pname})")
            self.lock_status_label.configure(
                text=f"Lock: Active on {pname}", text_color="#a6e3a1"
            )

    def _on_window_selected(self, choice: str):
        target = self.window_map.get(choice, "")
        self.engine.target_window = target
        if target:
            self.lock_status_label.configure(
                text=f"Lock: Active on {target}", text_color="#a6e3a1"
            )
        else:
            self.lock_status_label.configure(
                text="Lock: Inactive (Clicks work in any window)", text_color="#89b4fa"
            )

    def _on_trigger_mode_changed(self, choice: str):
        if "Hold" in choice:
            self.engine.hotkey_mode = "HOLD"
        else:
            self.engine.hotkey_mode = "TOGGLE"

    def _on_sched_toggle(self):
        self.engine.scheduler.enabled = self.sched_var.get()
        self._on_sched_time_changed()

    def _on_sched_time_changed(self, event=None):
        try:
            h = int(self.sched_h.get().strip() or "0")
            m = int(self.sched_m.get().strip() or "0")
            s = int(self.sched_s.get().strip() or "0")
            total = h * 3600 + m * 60 + s
            self.engine.scheduler.duration_seconds = float(total)
        except ValueError:
            pass

    def _on_sched_action_changed(self, choice: str):
        if "Sleep" in choice:
            self.engine.scheduler.action = self.engine.scheduler.ACTION_SLEEP
        elif "Shut Down" in choice:
            self.engine.scheduler.action = self.engine.scheduler.ACTION_SHUTDOWN
        elif "Alarm" in choice:
            self.engine.scheduler.action = self.engine.scheduler.ACTION_BEEP
        else:
            self.engine.scheduler.action = self.engine.scheduler.ACTION_STOP

    def _poll_timer_status(self):
        if self.engine.scheduler.enabled and self.engine.is_running:
            rem = self.engine.scheduler.format_remaining()
            self.timer_countdown_label.configure(
                text=f"Time Remaining: {rem}", text_color="#a6e3a1"
            )
        elif self.engine.scheduler.enabled:
            rem = self.engine.scheduler.format_remaining()
            self.timer_countdown_label.configure(
                text=f"Scheduled Duration: {rem}", text_color="#89b4fa"
            )
        else:
            self.timer_countdown_label.configure(
                text="Countdown: Disabled", text_color="#6c7086"
            )
        self.after(500, self._poll_timer_status)

    def _on_hotkey_changed(self, action_id: str, entry_widget):
        val = entry_widget.get().strip().lower()
        if val:
            self.hotkey_mgr.set_hotkey(action_id, val)

    def _on_sound_toggle(self):
        self.engine.sound_enabled = self.sound_var.get()

    def _on_topmost_toggle(self):
        if self.on_toggle_topmost:
            self.on_toggle_topmost(self.topmost_var.get())

    def _on_hud_toggle(self):
        if self.on_toggle_hud:
            self.on_toggle_hud(self.hud_var.get())

    def _load_selected_profile(self):
        name = self.preset_dropdown.get()
        data = ProfileManager.load_profile(name)
        if not data:
            return

        if "mode" in data:
            self.engine.mode = data["mode"]
        if "burst_config" in data:
            self.engine.burst_config.update(data["burst_config"])
        if "sequence_config" in data:
            self.engine.sequence_config.update(data["sequence_config"])
        if "pixel_config" in data:
            self.engine.pixel_config.update(data["pixel_config"])
        if "template_config" in data:
            self.engine.template_config.update(data["template_config"])
        if "keyspam_config" in data:
            self.engine.keyspam_config.update(data["keyspam_config"])

        self.save_status_label.configure(text=f"Loaded profile: {name}", text_color="#a6e3a1")
        if self.on_profile_loaded:
            self.on_profile_loaded()

    def _save_current_profile(self):
        name = self.profile_name_entry.get().strip()
        if not name:
            self.save_status_label.configure(text="Please enter a profile name", text_color="#f38ba8")
            return

        data = {
            "mode": self.engine.mode,
            "burst_config": self.engine.burst_config,
            "sequence_config": self.engine.sequence_config,
            "pixel_config": self.engine.pixel_config,
            "template_config": self.engine.template_config,
            "keyspam_config": self.engine.keyspam_config,
        }

        success = ProfileManager.save_profile(name, data)
        if success:
            self.save_status_label.configure(text=f"Profile '{name}' saved successfully!", text_color="#a6e3a1")
            self._refresh_profiles_list()
        else:
            self.save_status_label.configure(text="Failed to save profile", text_color="#f38ba8")

    def _create_desktop_shortcut(self):
        try:
            from create_shortcut import create_desktop_shortcut
            out = create_desktop_shortcut()
            self.shortcut_status_label.configure(
                text="✓ Shortcut created on Desktop!", text_color="#a6e3a1"
            )
        except Exception as e:
            self.shortcut_status_label.configure(
                text=f"Failed: {e}", text_color="#f38ba8"
            )

    def _check_for_updates(self):
        import webbrowser
        webbrowser.open_new_tab("https://github.com/Solf1re1/GhiLFm")
