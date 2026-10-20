"""
Multi-Point Sequence Tab.
Allows creating, ordering, and fine-tuning sequential click points
with individual delays, button types, jitter, and smooth Bezier glides.
"""

import customtkinter as ctk
from typing import List, Dict, Any, Optional
from apex_clicker.core.input_driver import InputDriver


class SequenceTab(ctk.CTkFrame):
    """Tab for multi-point sequence auto-clicking automation."""

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self.points: List[Dict[str, Any]] = self.engine.sequence_config.get("points", [])

        self._build_ui()
        self._refresh_points_list()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Control Bar
        top_bar = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        top_bar.grid(row=0, column=0, padx=8, pady=(8, 4), sticky="ew")

        # Action Buttons
        btn_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_frame.pack(side="left", padx=10, pady=6)

        add_curr_btn = ctk.CTkButton(
            btn_frame,
            text="📍 Add Cursor Pos [Ctrl+F8]",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            height=30,
            command=self.add_current_cursor_point,
        )
        add_curr_btn.pack(side="left", padx=(0, 6))

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="🧹 Clear All",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#313244",
            hover_color="#45475a",
            height=30,
            command=self.clear_all_points,
        )
        clear_btn.pack(side="left", padx=4)

        # Sequence Loop settings
        loop_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        loop_frame.pack(side="right", padx=10, pady=6)

        ctk.CTkLabel(loop_frame, text="Loops:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left", padx=4)
        self.loop_entry = ctk.CTkEntry(loop_frame, width=50, height=28, justify="center")
        self.loop_entry.insert(0, "0")
        self.loop_entry.pack(side="left", padx=4)
        self.loop_entry.bind("<KeyRelease>", self._on_loop_changed)
        ctk.CTkLabel(loop_frame, text="(0 = inf)", font=ctk.CTkFont(size=10), text_color="#6c7086").pack(side="left")

        # Points Scrollable Container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#181825",
            corner_radius=10,
            border_width=1,
            border_color="#313244",
        )
        self.scroll_frame.grid(row=1, column=0, padx=8, pady=4, sticky="nsew")

        # Manual Point Insertion Bar
        bottom_bar = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        bottom_bar.grid(row=2, column=0, padx=8, pady=(4, 8), sticky="ew")

        ctk.CTkLabel(bottom_bar, text="Manual Point:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#cdd6f4").pack(side="left", padx=(10, 4), pady=6)

        ctk.CTkLabel(bottom_bar, text="X:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left", padx=2)
        self.manual_x = ctk.CTkEntry(bottom_bar, width=50, height=26, justify="center")
        self.manual_x.insert(0, "500")
        self.manual_x.pack(side="left", padx=2)

        ctk.CTkLabel(bottom_bar, text="Y:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left", padx=2)
        self.manual_y = ctk.CTkEntry(bottom_bar, width=50, height=26, justify="center")
        self.manual_y.insert(0, "400")
        self.manual_y.pack(side="left", padx=2)

        ctk.CTkLabel(bottom_bar, text="Action:", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left", padx=(4, 2))
        self.manual_btn = ctk.CTkOptionMenu(bottom_bar, values=["left", "right", "double"], width=75, height=26)
        self.manual_btn.pack(side="left", padx=2)
        self.manual_btn.set("left")

        ctk.CTkLabel(bottom_bar, text="Delay(s):", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(side="left", padx=(4, 2))
        self.manual_delay = ctk.CTkEntry(bottom_bar, width=45, height=26, justify="center")
        self.manual_delay.insert(0, "0.2")
        self.manual_delay.pack(side="left", padx=2)

        add_manual_btn = ctk.CTkButton(
            bottom_bar,
            text="➕ Add",
            width=60,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            command=self.add_manual_point,
        )
        add_manual_btn.pack(side="left", padx=8)

    def _refresh_points_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.points:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="No target coordinates added yet.\nPress 'Add Cursor Pos [Ctrl+F8]' or enter manual points below.",
                font=ctk.CTkFont(size=13),
                text_color="#6c7086",
                justify="center",
            )
            empty_lbl.pack(pady=40)
            return

        for idx, pt in enumerate(self.points):
            row = ctk.CTkFrame(self.scroll_frame, fg_color="#1e1e2e", corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)

            # Index badge
            idx_badge = ctk.CTkLabel(
                row,
                text=f"#{idx + 1}",
                width=32,
                font=ctk.CTkFont(weight="bold"),
                text_color="#89b4fa",
            )
            idx_badge.pack(side="left", padx=(8, 4), pady=6)

            # Coordinate
            coord_str = f"({pt.get('x', 0)}, {pt.get('y', 0)})"
            ctk.CTkLabel(
                row,
                text=coord_str,
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                width=110,
                anchor="w",
            ).pack(side="left", padx=4)

            # Button
            btn_type = pt.get("button", "left").upper()
            ctk.CTkLabel(row, text=f"[{btn_type}]", font=ctk.CTkFont(size=11), text_color="#f9e2af", width=70).pack(
                side="left", padx=4
            )

            # Delay
            delay = pt.get("delay", 0.2)
            ctk.CTkLabel(row, text=f"{delay:.2f}s delay", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(
                side="left", padx=8
            )

            # Delete button
            del_btn = ctk.CTkButton(
                row,
                text="✖",
                width=28,
                height=24,
                fg_color="#313244",
                hover_color="#f38ba8",
                text_color="#f38ba8",
                command=lambda i=idx: self.delete_point(i),
            )
            del_btn.pack(side="right", padx=(4, 8), pady=4)

    def add_current_cursor_point(self):
        """Captures mouse cursor and appends to points list."""
        x, y = InputDriver.get_cursor_pos()
        new_pt = {
            "x": x,
            "y": y,
            "button": "left",
            "delay": 0.2,
            "jitter_radius": 2,
            "smooth_move": True,
            "move_duration": 0.2,
        }
        self.points.append(new_pt)
        self.engine.sequence_config["points"] = self.points
        self._refresh_points_list()

    def add_manual_point(self):
        try:
            x = int(self.manual_x.get().strip() or "0")
            y = int(self.manual_y.get().strip() or "0")
            btn = self.manual_btn.get().lower()
            delay = float(self.manual_delay.get().strip() or "0.2")

            new_pt = {
                "x": x,
                "y": y,
                "button": btn,
                "delay": max(0.01, delay),
                "jitter_radius": 2,
                "smooth_move": True,
                "move_duration": 0.2,
            }
            self.points.append(new_pt)
            self.engine.sequence_config["points"] = self.points
            self._refresh_points_list()
        except ValueError:
            pass

    def delete_point(self, index: int):
        if 0 <= index < len(self.points):
            self.points.pop(index)
            self.engine.sequence_config["points"] = self.points
            self._refresh_points_list()

    def clear_all_points(self):
        self.points.clear()
        self.engine.sequence_config["points"] = self.points
        self._refresh_points_list()

    def _on_loop_changed(self, event=None):
        try:
            val = int(self.loop_entry.get().strip() or "0")
            self.engine.sequence_config["repeat_count"] = max(0, val)
        except ValueError:
            pass
