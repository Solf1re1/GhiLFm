"""
Floating Mini HUD Overlay.
A compact, draggable, semi-transparent always-on-top status widget.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional


class MiniHudOverlay(ctk.CTkToplevel):
    """Semi-transparent floating mini overlay widget."""

    def __init__(self, master, on_toggle_click=None):
        super().__init__(master)

        self.on_toggle_click = on_toggle_click

        # Window settings
        self.overrideredirect(True)  # Frameless
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.88)
        self.geometry("235x70+40+40")
        self.configure(fg_color="#181825")

        # Dragging mechanics
        self._drag_data = {"x": 0, "y": 0}
        self.bind("<Button-1>", self._start_drag)
        self.bind("<B1-Motion>", self._on_drag)

        # Layout Container
        self.frame = ctk.CTkFrame(
            self,
            fg_color="#1e1e2e",
            corner_radius=10,
            border_width=1,
            border_color="#45475a",
        )
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.frame.bind("<Button-1>", self._start_drag)
        self.frame.bind("<B1-Motion>", self._on_drag)

        # Status row
        self.status_label = ctk.CTkLabel(
            self.frame,
            text="● IDLE [Ctrl+F6]",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#a6adc8",
        )
        self.status_label.pack(side="top", anchor="w", padx=10, pady=(6, 0))
        self.status_label.bind("<Button-1>", self._start_drag)
        self.status_label.bind("<B1-Motion>", self._on_drag)

        # Stats row
        self.stats_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.stats_frame.pack(side="top", fill="x", padx=10, pady=(2, 6))
        self.stats_frame.bind("<Button-1>", self._start_drag)
        self.stats_frame.bind("<B1-Motion>", self._on_drag)

        self.cps_label = ctk.CTkLabel(
            self.stats_frame,
            text="0 CPS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#89b4fa",
        )
        self.cps_label.pack(side="left")

        self.clicks_label = ctk.CTkLabel(
            self.stats_frame,
            text="0 Clicks",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#cdd6f4",
        )
        self.clicks_label.pack(side="right")

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def update_stats(self, is_running: bool, is_paused: bool, cps: float, clicks: int):
        """Updates the status and counter displays."""
        if is_running:
            if is_paused:
                self.status_label.configure(text="● PAUSED [Ctrl+F7]", text_color="#f9e2af")
            else:
                self.status_label.configure(text="● ACTIVE [Ctrl+F6]", text_color="#a6e3a1")
        else:
            self.status_label.configure(text="● STOPPED [Ctrl+F6]", text_color="#f38ba8")

        self.cps_label.configure(text=f"{int(round(cps))} CPS")
        self.clicks_label.configure(text=f"{clicks:,} Clicks")
