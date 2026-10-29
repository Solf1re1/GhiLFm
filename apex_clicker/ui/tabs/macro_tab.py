"""
Macro Recorder & Player Tab.
Enables real-time recording of mouse actions and keystrokes,
playback speed scaling, looping, and JSON import/export.
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import Optional
from apex_clicker.core.macro_recorder import MacroEngine


class MacroTab(ctk.CTkScrollableFrame):
    """Tab for macro recording and playback orchestration."""

    def __init__(self, master, macro_engine: MacroEngine):
        super().__init__(master, fg_color="transparent")
        self.macro_engine = macro_engine

        self._build_ui()
        self.macro_engine.on_record_event = self._on_record_count_update
        self.macro_engine.on_state_change = self._on_state_change

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="macro_col")

        # --- LEFT CARD: Recording Studio ---
        rec_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        rec_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        ctk.CTkLabel(
            rec_card,
            text="⏺️ Macro Recording Studio",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Record Button
        self.record_btn = ctk.CTkButton(
            rec_card,
            text="⏺️ Start Recording [Ctrl+F10]",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#f38ba8",
            text_color="#11111b",
            hover_color="#eba0ac",
            height=34,
            command=self._toggle_recording,
        )
        self.record_btn.pack(fill="x", padx=14, pady=(6, 8))

        # Track mouse moves switch
        self.track_moves_var = ctk.BooleanVar(value=False)
        moves_cb = ctk.CTkSwitch(
            rec_card,
            text="Record Cursor Movements",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            variable=self.track_moves_var,
            progress_color="#89b4fa",
        )
        moves_cb.pack(anchor="w", padx=14, pady=(2, 8))

        # Events counter display
        stats_frame = ctk.CTkFrame(rec_card, fg_color="#1e1e2e", corner_radius=8)
        stats_frame.pack(fill="x", padx=14, pady=(4, 10))

        self.event_count_label = ctk.CTkLabel(
            stats_frame,
            text="Recorded Events: 0",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#89b4fa",
        )
        self.event_count_label.pack(padx=10, pady=8)

        # File Import/Export
        file_row = ctk.CTkFrame(rec_card, fg_color="transparent")
        file_row.pack(fill="x", padx=14, pady=(2, 12))
        file_row.grid_columnconfigure((0, 1), weight=1)

        save_btn = ctk.CTkButton(
            file_row,
            text="💾 Save Macro",
            width=0,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            command=self._save_macro_dialog,
        )
        save_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        load_btn = ctk.CTkButton(
            file_row,
            text="📂 Load Macro",
            width=0,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            command=self._load_macro_dialog,
        )
        load_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # --- RIGHT CARD: Playback Station ---
        play_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        play_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        ctk.CTkLabel(
            play_card,
            text="▶️ Playback Station",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Play Button
        self.play_btn = ctk.CTkButton(
            play_card,
            text="▶️ Play Macro",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#a6e3a1",
            text_color="#11111b",
            hover_color="#94e2d5",
            height=34,
            command=self._toggle_playback,
        )
        self.play_btn.pack(fill="x", padx=14, pady=(6, 8))

        # Speed Multiplier
        speed_header = ctk.CTkFrame(play_card, fg_color="transparent")
        speed_header.pack(fill="x", padx=14, pady=(4, 0))
        ctk.CTkLabel(speed_header, text="Playback Speed:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cdd6f4").pack(side="left")
        self.speed_val_label = ctk.CTkLabel(speed_header, text="1.0x", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89b4fa")
        self.speed_val_label.pack(side="right")

        self.speed_slider = ctk.CTkSlider(
            play_card,
            from_=0.25,
            to=4.0,
            number_of_steps=15,
            command=self._on_speed_slider_changed,
        )
        self.speed_slider.pack(fill="x", padx=14, pady=(2, 8))
        self.speed_slider.set(1.0)

        # Loop count
        loop_row = ctk.CTkFrame(play_card, fg_color="transparent")
        loop_row.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkLabel(loop_row, text="Replay Loops:", font=ctk.CTkFont(weight="bold"), text_color="#cdd6f4").pack(side="left")
        self.loop_entry = ctk.CTkEntry(loop_row, width=60, justify="center")
        self.loop_entry.insert(0, "1")
        self.loop_entry.pack(side="left", padx=8)
        ctk.CTkLabel(loop_row, text="(0 = infinite)", font=ctk.CTkFont(size=11), text_color="#6c7086").pack(side="left")

    def _toggle_recording(self):
        if self.macro_engine.is_playing:
            return
        if self.macro_engine.is_recording:
            self.macro_engine.stop_recording()
        else:
            self.macro_engine.start_recording(record_mouse_moves=self.track_moves_var.get())

    def _toggle_playback(self):
        if self.macro_engine.is_playing:
            self.macro_engine.stop_playback()
        else:
            speed = float(self.speed_slider.get())
            try:
                loops = int(self.loop_entry.get().strip() or "1")
            except ValueError:
                loops = 1
            self.macro_engine.start_playback(speed_multiplier=speed, repeat_count=loops)

    def _on_speed_slider_changed(self, value):
        val = round(value, 2)
        self.speed_val_label.configure(text=f"{val}x")

    def _on_record_count_update(self, count: int):
        self.after(0, lambda: self.event_count_label.configure(text=f"Recorded Events: {count:,}"))

    def _on_state_change(self, is_recording: bool, is_playing: bool):
        def _update():
            if is_recording:
                self.record_btn.configure(text="⏹️ Stop Recording [Ctrl+F10]", fg_color="#f38ba8")
                self.play_btn.configure(state="disabled")
            else:
                self.record_btn.configure(text="⏺️ Start Recording [Ctrl+F10]", fg_color="#f38ba8")
                self.play_btn.configure(state="normal")

            if is_playing:
                self.play_btn.configure(text="⏹️ Stop Playback", fg_color="#f38ba8")
                self.record_btn.configure(state="disabled")
            else:
                self.play_btn.configure(text="▶️ Play Macro", fg_color="#a6e3a1")
                self.record_btn.configure(state="normal")
        self.after(0, _update)

    def _save_macro_dialog(self):
        if not self.macro_engine.events:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Macro File",
        )
        if path:
            self.macro_engine.save_to_file(path)

    def _load_macro_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Load Macro File",
        )
        if path:
            self.macro_engine.load_from_file(path)
            self.event_count_label.configure(text=f"Recorded Events: {len(self.macro_engine.events):,}")
