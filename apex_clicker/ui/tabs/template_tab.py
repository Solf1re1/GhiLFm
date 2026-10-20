"""
Visual Template & Image Matching Tab.
Enables visual bot clicking: searches the screen for target image/button templates
and automatically clicks their center.
Supports single and multi-template searching, clipboard snipping (Win+Shift+S),
recent template history, and Exact vs Similar precision modes.
"""

import os
import time
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageGrab
from typing import List, Dict, Any, Optional
from apex_clicker.core.template_matcher import TemplateMatcher
from apex_clicker.core.input_driver import InputDriver


class TemplateTab(ctk.CTkScrollableFrame):
    """Tab for visual image template detection, multi-target queue, and auto-clicking."""

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")
        self.engine = engine
        self._updating = False

        # Multi-template list: List of dicts
        # {"id": str, "name": str, "path": str, "width": int, "height": int, "enabled": bool, "thumb": ctk.CTkImage}
        self.templates: List[Dict[str, Any]] = []

        # Assets templates directory
        self.assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "assets",
            "templates",
        )
        os.makedirs(self.assets_dir, exist_ok=True)

        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1, uniform="tpl_col")

        # =========================================================================
        # --- LEFT CARD: Template Library & Multi-Target Queue ---
        # =========================================================================
        left_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        left_card.grid(row=0, column=0, padx=(8, 4), pady=8, sticky="nsew")

        ctk.CTkLabel(
            left_card,
            text="🖼️ Target Templates & Multi-Target Queue",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Import Buttons Row: Paste from Clipboard & Browse File
        btn_box = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_box.pack(fill="x", padx=14, pady=(4, 4))
        btn_box.grid_columnconfigure((0, 1), weight=1)

        self.clip_btn = ctk.CTkButton(
            btn_box,
            text="📋 Paste Clipboard",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            height=32,
            command=self._import_from_clipboard,
        )
        self.clip_btn.grid(row=0, column=0, padx=(0, 3), sticky="ew")

        self.file_btn = ctk.CTkButton(
            btn_box,
            text="📂 Add from File...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#313244",
            hover_color="#45475a",
            height=32,
            command=self._choose_template_file,
        )
        self.file_btn.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        # Tip
        ctk.CTkLabel(
            left_card,
            text="💡 Tip: Press Win+Shift+S to snip an element, then click Paste (or Ctrl+V). Add multiple targets to search simultaneously!",
            font=ctk.CTkFont(size=10),
            text_color="#6c7086",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # Queue Management Header
        queue_hdr = ctk.CTkFrame(left_card, fg_color="transparent")
        queue_hdr.pack(fill="x", padx=14, pady=(4, 2))

        self.queue_count_lbl = ctk.CTkLabel(
            queue_hdr,
            text="TARGETS (0 Active)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#89b4fa",
        )
        self.queue_count_lbl.pack(side="left")

        clear_btn = ctk.CTkButton(
            queue_hdr,
            text="Clear All",
            width=58,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#313244",
            hover_color="#f38ba8",
            text_color="#cdd6f4",
            command=self._clear_all_templates,
        )
        clear_btn.pack(side="right", padx=(4, 0))

        sel_all_btn = ctk.CTkButton(
            queue_hdr,
            text="Select All",
            width=58,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#cdd6f4",
            command=self._select_all_templates,
        )
        sel_all_btn.pack(side="right")

        # Scrollable container for template cards/rows
        self.queue_frame = ctk.CTkScrollableFrame(
            left_card,
            fg_color="#181825",
            corner_radius=8,
            border_width=1,
            border_color="#313244",
            height=160,
        )
        self.queue_frame.pack(fill="x", padx=14, pady=(2, 8))

        # Overall Action Buttons Row: Test & Click vs Scan Only
        test_actions = ctk.CTkFrame(left_card, fg_color="transparent")
        test_actions.pack(fill="x", padx=14, pady=(2, 4))
        test_actions.grid_columnconfigure((0, 1), weight=1)

        self.test_click_btn = ctk.CTkButton(
            test_actions,
            text="🎯 Test & Click Target",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#89b4fa",
            text_color="#11111b",
            hover_color="#b4befe",
            height=32,
            command=self._test_and_click_now,
        )
        self.test_click_btn.grid(row=0, column=0, padx=(0, 3), sticky="ew")

        self.test_scan_btn = ctk.CTkButton(
            test_actions,
            text="🔍 Scan Only",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#cdd6f4",
            height=32,
            command=self._test_search_now,
        )
        self.test_scan_btn.grid(row=0, column=1, padx=(3, 0), sticky="ew")

        self.test_status_label = ctk.CTkLabel(
            left_card,
            text="Ready. Add or paste template images to begin.",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
            wraplength=340,
            justify="left",
        )
        self.test_status_label.pack(anchor="w", padx=14, pady=(0, 6))

        # Helpful hint about window positioning
        ctk.CTkLabel(
            left_card,
            text="💡 Tip: If your target is covered by ApexClicker, move this window to your 2nd monitor or enable Auto-minimize on the right.",
            font=ctk.CTkFont(size=10),
            text_color="#6c7086",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # =========================================================================
        # --- RIGHT CARD: Match Sensitivity & Execution Settings ---
        # =========================================================================
        right_card = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        right_card.grid(row=0, column=1, padx=(4, 8), pady=8, sticky="nsew")

        ctk.CTkLabel(
            right_card,
            text="⚙️ Match Precision & Execution",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        # Match Precision Mode (Exact vs Similar Switch)
        ctk.CTkLabel(
            right_card,
            text="Match Precision Mode:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.precision_seg = ctk.CTkSegmentedButton(
            right_card,
            values=["🎯 Exact (95%)", "🔍 Similar (60%)"],
            command=self._on_precision_mode_selected,
        )
        self.precision_seg.pack(fill="x", padx=14, pady=(2, 4))
        self.precision_seg.set("🔍 Similar (60%)")

        self.precision_desc_label = ctk.CTkLabel(
            right_card,
            text="Similar (60%): Flexible matching for buttons with glowing, transparency, or animations.",
            font=ctk.CTkFont(size=10),
            text_color="#6c7086",
            justify="left",
            wraplength=340,
        )
        self.precision_desc_label.pack(anchor="w", padx=14, pady=(0, 8))

        # Fine-Tuning Confidence Slider
        conf_header = ctk.CTkFrame(right_card, fg_color="transparent")
        conf_header.pack(fill="x", padx=14, pady=(2, 2))
        ctk.CTkLabel(
            conf_header,
            text="Fine-Tune Threshold:",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
        ).pack(side="left")

        self.conf_val_label = ctk.CTkLabel(
            conf_header,
            text="60% (Similar)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#89b4fa",
        )
        self.conf_val_label.pack(side="right")

        self.conf_slider = ctk.CTkSlider(
            right_card,
            from_=40,
            to=99,
            number_of_steps=59,
            command=self._on_conf_slider_changed,
        )
        self.conf_slider.pack(fill="x", padx=14, pady=(2, 8))
        self.conf_slider.set(60)

        # Divider
        ctk.CTkFrame(right_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=4)

        # Mouse Click Action
        ctk.CTkLabel(
            right_card,
            text="Click Action on Detection:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.btn_selector = ctk.CTkOptionMenu(
            right_card,
            values=[
                "double (Double Click - Open App)",
                "left (Single Click)",
                "right (Right Click)",
            ],
            command=self._on_btn_changed,
        )
        self.btn_selector.pack(fill="x", padx=14, pady=(2, 6))
        self.btn_selector.set("double (Double Click - Open App)")

        # Mouse Cursor Travel Style ("Move Over" vs Instant Jump)
        ctk.CTkLabel(
            right_card,
            text="🖱️ Cursor Travel to Target:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(4, 2))

        self.smooth_move_var = ctk.BooleanVar(value=True)
        self.smooth_move_cb = ctk.CTkCheckBox(
            right_card,
            text='Smooth travel ("Move over" instead of jumping)',
            variable=self.smooth_move_var,
            command=self._on_smooth_move_changed,
            font=ctk.CTkFont(size=11),
            checkbox_width=18,
            checkbox_height=18,
            fg_color="#89b4fa",
            hover_color="#b4befe",
        )
        self.smooth_move_cb.pack(anchor="w", padx=14, pady=(2, 4))

        self.move_speed_seg = ctk.CTkSegmentedButton(
            right_card,
            values=["⚡ Fast (0.15s)", "🎯 Smooth (0.25s)", "🐢 Gentle (0.40s)"],
            command=self._on_move_speed_changed,
        )
        self.move_speed_seg.pack(fill="x", padx=14, pady=(2, 3))
        self.move_speed_seg.set("🎯 Smooth (0.25s)")

        self.travel_desc_lbl = ctk.CTkLabel(
            right_card,
            text='💡 Glides cursor over to icon naturally so Windows registers hover focus before clicking.',
            font=ctk.CTkFont(size=10),
            text_color="#a6e3a1",
            justify="left",
            wraplength=340,
        )
        self.travel_desc_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        # Cooldown & Scan Interval Row
        timing_row = ctk.CTkFrame(right_card, fg_color="transparent")
        timing_row.pack(fill="x", padx=14, pady=4)
        timing_row.grid_columnconfigure((0, 1), weight=1)

        cd_box = ctk.CTkFrame(timing_row, fg_color="transparent")
        cd_box.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkLabel(cd_box, text="Cooldown (s):", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w")
        self.cooldown_entry = ctk.CTkEntry(cd_box, height=26, justify="center")
        self.cooldown_entry.insert(0, "0.5")
        self.cooldown_entry.pack(fill="x", pady=(2, 0))
        self.cooldown_entry.bind("<KeyRelease>", self._on_cooldown_changed)

        intv_box = ctk.CTkFrame(timing_row, fg_color="transparent")
        intv_box.grid(row=0, column=1, padx=(4, 0), sticky="ew")
        ctk.CTkLabel(intv_box, text="Scan Interval (s):", font=ctk.CTkFont(size=11), text_color="#a6adc8").pack(anchor="w")
        self.interval_entry = ctk.CTkEntry(intv_box, height=26, justify="center")
        self.interval_entry.insert(0, "0.10")
        self.interval_entry.pack(fill="x", pady=(2, 0))
        self.interval_entry.bind("<KeyRelease>", self._on_interval_changed)

        # Divider
        ctk.CTkFrame(right_card, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=6)

        # Multi-Target Queue Flow & Missing Target Behavior
        ctk.CTkLabel(
            right_card,
            text="🔀 Multi-Target Queue Flow:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=14, pady=(2, 2))

        self.flow_mode_seg = ctk.CTkSegmentedButton(
            right_card,
            values=["⚡ Any Match", "🔢 Ordered Steps (1➔2➔3)"],
            command=self._on_flow_mode_changed,
        )
        self.flow_mode_seg.pack(fill="x", padx=14, pady=(2, 4))
        self.flow_mode_seg.set("⚡ Any Match")

        self.flow_behavior_lbl = ctk.CTkLabel(
            right_card,
            text="If Current Target is Not Found:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#cdd6f4",
        )
        self.flow_behavior_lbl.pack(anchor="w", padx=14, pady=(4, 2))

        self.not_found_seg = ctk.CTkSegmentedButton(
            right_card,
            values=["⏳ Wait then Proceed", "⏭️ Go to Next Target"],
            command=self._on_not_found_mode_changed,
        )
        self.not_found_seg.pack(fill="x", padx=14, pady=(2, 3))
        self.not_found_seg.set("⏳ Wait then Proceed")

        self.flow_desc_label = ctk.CTkLabel(
            right_card,
            text="⏳ Wait then Proceed: Waits until target appears on screen, clicks it, then moves to next step.",
            font=ctk.CTkFont(size=10),
            text_color="#a6e3a1",
            justify="left",
            wraplength=340,
        )
        self.flow_desc_label.pack(anchor="w", padx=14, pady=(0, 6))

        # Loop sequence checkbox
        self.loop_queue_var = ctk.BooleanVar(value=True)
        self.loop_queue_cb = ctk.CTkCheckBox(
            right_card,
            text="🔁 Repeat queue continuously (loop 1 ➔ 2 ➔ 3)",
            variable=self.loop_queue_var,
            command=self._on_loop_queue_changed,
            font=ctk.CTkFont(size=11),
            checkbox_width=18,
            checkbox_height=18,
            fg_color="#89b4fa",
            hover_color="#b4befe",
        )
        self.loop_queue_cb.pack(anchor="w", padx=14, pady=(2, 6))

        # Auto-Minimize Checkbox & Hint
        self.auto_minimize_var = ctk.BooleanVar(value=True)
        self.auto_minimize_cb = ctk.CTkCheckBox(
            right_card,
            text="Auto-minimize window when bot starts",
            variable=self.auto_minimize_var,
            font=ctk.CTkFont(size=11),
            checkbox_width=18,
            checkbox_height=18,
            fg_color="#89b4fa",
            hover_color="#b4befe",
        )
        self.auto_minimize_cb.pack(anchor="w", padx=14, pady=(6, 2))

        ctk.CTkLabel(
            right_card,
            text="💡 Minimizes ApexClicker to keep your game/screen completely clear.",
            font=ctk.CTkFont(size=10),
            text_color="#6c7086",
            justify="left",
            wraplength=340,
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # Start / Stop Visual Bot Button
        self.start_stop_btn = ctk.CTkButton(
            right_card,
            text="▶️ START VISUAL BOT [Win+*]",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#a6e3a1",
            text_color="#11111b",
            hover_color="#94e2d5",
            height=38,
            command=self._toggle_bot_running,
        )
        self.start_stop_btn.pack(fill="x", padx=14, pady=(6, 12))

    # =========================================================================
    # --- Template Management & Rendering ---
    # =========================================================================
    def _refresh_queue_display(self):
        """Rebuilds the list of template items inside queue_frame."""
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        active_count = sum(1 for t in self.templates if t.get("enabled", True))
        total_count = len(self.templates)
        self.queue_count_lbl.configure(text=f"TARGETS ({active_count} of {total_count} Active)")

        if not self.templates:
            empty_box = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
            empty_box.pack(fill="both", expand=True, pady=30)
            ctk.CTkLabel(
                empty_box,
                text="No target images in queue.\nClick 'Paste Clipboard' or press Ctrl+V to add.",
                font=ctk.CTkFont(size=11),
                text_color="#6c7086",
                justify="center",
            ).pack()
            return

        for idx, tpl in enumerate(self.templates):
            row = ctk.CTkFrame(self.queue_frame, fg_color="#1e1e2e", corner_radius=6)
            row.pack(fill="x", padx=2, pady=2)

            # Step number badge (#1, #2, #3...)
            step_lbl = ctk.CTkLabel(
                row,
                text=f"#{idx+1}",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#89b4fa",
                width=24,
            )
            step_lbl.pack(side="left", padx=(6, 2))

            # Checkbox for enabled state
            chk_var = ctk.BooleanVar(value=tpl.get("enabled", True))
            chk = ctk.CTkCheckBox(
                row,
                text="",
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                variable=chk_var,
                command=lambda t=tpl, v=chk_var: self._toggle_template_state(t, v.get()),
            )
            chk.pack(side="left", padx=(2, 4), pady=4)

            # Thumbnail
            thumb = tpl.get("thumb")
            if thumb:
                thumb_lbl = ctk.CTkLabel(row, image=thumb, text="", width=40, height=28)
                thumb_lbl.pack(side="left", padx=2)

            # Name & dimensions info
            w = tpl.get("width", 0)
            h = tpl.get("height", 0)
            name = tpl.get("name", f"Target #{idx+1}")
            info_lbl = ctk.CTkLabel(
                row,
                text=f"{name}\n({w}x{h} px)",
                font=ctk.CTkFont(size=10),
                text_color="#cdd6f4",
                anchor="w",
                justify="left",
            )
            info_lbl.pack(side="left", padx=6, fill="x", expand=True)

            # Delete button (✖)
            del_btn = ctk.CTkButton(
                row,
                text="✖",
                width=22,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#313244",
                hover_color="#f38ba8",
                text_color="#f38ba8",
                command=lambda i=idx: self._delete_template(i),
            )
            del_btn.pack(side="right", padx=(2, 6), pady=4)

            # Move Down (▼)
            is_last = (idx >= len(self.templates) - 1)
            down_btn = ctk.CTkButton(
                row,
                text="▼",
                width=22,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#313244" if not is_last else "#232334",
                hover_color="#45475a",
                text_color="#cdd6f4" if not is_last else "#585b70",
                state="normal" if not is_last else "disabled",
                command=lambda i=idx: self._move_template_down(i),
            )
            down_btn.pack(side="right", padx=1, pady=4)

            # Move Up (▲)
            is_first = (idx == 0)
            up_btn = ctk.CTkButton(
                row,
                text="▲",
                width=22,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#313244" if not is_first else "#232334",
                hover_color="#45475a",
                text_color="#cdd6f4" if not is_first else "#585b70",
                state="normal" if not is_first else "disabled",
                command=lambda i=idx: self._move_template_up(i),
            )
            up_btn.pack(side="right", padx=1, pady=4)

            # Test & Click button
            click_btn = ctk.CTkButton(
                row,
                text="🎯 Click",
                width=48,
                height=22,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#89b4fa",
                hover_color="#b4befe",
                text_color="#11111b",
                command=lambda t=tpl: self._test_single_template(t, and_click=True),
            )
            click_btn.pack(side="right", padx=2, pady=4)

            # Scan only button
            scan_btn = ctk.CTkButton(
                row,
                text="Scan",
                width=38,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="#313244",
                hover_color="#45475a",
                text_color="#cdd6f4",
                command=lambda t=tpl: self._test_single_template(t, and_click=False),
            )
            scan_btn.pack(side="right", padx=2, pady=4)

    def _move_template_up(self, index: int):
        """Moves target higher in the sequence order."""
        if index > 0 and index < len(self.templates):
            self.templates[index - 1], self.templates[index] = self.templates[index], self.templates[index - 1]
            self.engine.template_config["templates"] = self.templates
            self._refresh_queue_display()

    def _move_template_down(self, index: int):
        """Moves target lower in the sequence order."""
        if index >= 0 and index < len(self.templates) - 1:
            self.templates[index + 1], self.templates[index] = self.templates[index], self.templates[index + 1]
            self.engine.template_config["templates"] = self.templates
            self._refresh_queue_display()

    def _add_template_to_library(self, file_path: str, name: Optional[str] = None):
        """Loads an image file, creates thumbnail, and appends to self.templates."""
        if not os.path.exists(file_path):
            return

        try:
            pil_img = Image.open(file_path)
            w, h = pil_img.size

            # Create thumbnail for UI list
            pil_thumb = pil_img.copy()
            pil_thumb.thumbnail((40, 28))
            ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=pil_thumb.size)

            display_name = name or os.path.basename(file_path)
            # Remove extension for cleaner title if file
            if display_name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                display_name = os.path.splitext(display_name)[0]

            tpl_data = {
                "id": f"tpl_{int(time.time() * 1000)}_{len(self.templates) + 1}",
                "name": display_name,
                "path": file_path,
                "width": w,
                "height": h,
                "enabled": True,
                "thumb": ctk_thumb,
                "cached": None,
            }

            # Avoid immediate duplicate paths
            existing = [t for t in self.templates if t.get("path") == file_path]
            if not existing:
                self.templates.insert(0, tpl_data)  # Put newest template at the top (Step #1)
                # Keep library to most recent 10 templates
                if len(self.templates) > 10:
                    self.templates.pop()

            self.engine.template_config["templates"] = self.templates
            self.engine.template_config["template_path"] = file_path
            self._refresh_queue_display()
        except Exception as e:
            self.test_status_label.configure(
                text=f"Failed to load image: {e}",
                text_color="#f38ba8",
            )

    def _toggle_template_state(self, tpl: Dict[str, Any], enabled: bool):
        tpl["enabled"] = enabled
        self.engine.template_config["templates"] = self.templates
        active_count = sum(1 for t in self.templates if t.get("enabled", True))
        self.queue_count_lbl.configure(text=f"TARGETS ({active_count} of {len(self.templates)} Active)")

    def _delete_template(self, index: int):
        if 0 <= index < len(self.templates):
            removed = self.templates.pop(index)
            self.engine.template_config["templates"] = self.templates
            self._refresh_queue_display()
            self.test_status_label.configure(
                text=f"Removed '{removed.get('name', 'Target')}' from library.",
                text_color="#a6adc8",
            )

    def _select_all_templates(self):
        for t in self.templates:
            t["enabled"] = True
        self.engine.template_config["templates"] = self.templates
        self._refresh_queue_display()

    def _clear_all_templates(self):
        self.templates.clear()
        self.engine.template_config["templates"] = []
        self._refresh_queue_display()
        self.test_status_label.configure(
            text="Template library cleared.",
            text_color="#a6adc8",
        )

    # =========================================================================
    # --- Import / Clipboard Mechanics ---
    # =========================================================================
    def _import_from_clipboard(self):
        """Grabs an image directly from the Windows clipboard (e.g. from Win+Shift+S snip)."""
        try:
            clip = ImageGrab.grabclipboard()
        except Exception as e:
            self.test_status_label.configure(
                text=f"Clipboard error: {e}",
                text_color="#f38ba8",
            )
            return

        if clip is None:
            self.test_status_label.configure(
                text="⚠️ No image on clipboard! Press Win+Shift+S to snip an image first.",
                text_color="#f9e2af",
            )
            return

        # Case 1: Direct Image Object (Snipping Tool, Paint, browser copy)
        if isinstance(clip, Image.Image):
            filename = f"snip_{int(time.time())}_{len(self.templates) + 1}.png"
            save_path = os.path.join(self.assets_dir, filename)

            try:
                clip.save(save_path, "PNG")
                w, h = clip.size
                name = f"Snip #{len(self.templates) + 1}"
                self._add_template_to_library(save_path, name=name)
                self.test_status_label.configure(
                    text=f"✓ Added target from clipboard: {name} ({w}x{h} px)!",
                    text_color="#a6e3a1",
                )
            except Exception as e:
                self.test_status_label.configure(
                    text=f"Failed to save clipboard image: {e}",
                    text_color="#f38ba8",
                )
            return

        # Case 2: File copied from Windows Explorer
        if isinstance(clip, list):
            valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
            image_files = [f for f in clip if isinstance(f, str) and f.lower().endswith(valid_exts) and os.path.exists(f)]
            if image_files:
                for f in image_files[:4]:  # Support importing multiple files at once
                    self._add_template_to_library(f)
                self.test_status_label.configure(
                    text=f"✓ Added {len(image_files[:4])} image(s) from clipboard!",
                    text_color="#a6e3a1",
                )
                return
            else:
                self.test_status_label.configure(
                    text="⚠️ Clipboard has files, but none are images (.png/.jpg).",
                    text_color="#f9e2af",
                )
                return

        self.test_status_label.configure(
            text="⚠️ Clipboard does not contain an image. Press Win+Shift+S first.",
            text_color="#f9e2af",
        )

    def _choose_template_file(self):
        paths = filedialog.askopenfilenames(
            title="Select Target Image(s)",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")],
        )
        if paths:
            for p in paths:
                self._add_template_to_library(p)
            self.test_status_label.configure(
                text=f"✓ Added {len(paths)} template image(s) to queue!",
                text_color="#a6e3a1",
            )

    # =========================================================================
    # --- Testing & Matching ---
    # =========================================================================
    def _test_single_template(self, tpl: Dict[str, Any], and_click: bool = False):
        """Tests screen search for a specific template, optionally clicking it."""
        p = tpl.get("path", "")
        if not p or not os.path.exists(p):
            self.test_status_label.configure(text=f"Template file not found: {p}", text_color="#f38ba8")
            return

        tpl_img = TemplateMatcher.load_template_file(p)
        conf = float(self.conf_slider.get()) / 100.0
        name = tpl.get("name", "Target")

        exclude = None
        try:
            root = self.winfo_toplevel()
            if root and root.state() != "iconic":
                exclude = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height())
        except Exception:
            pass

        match = TemplateMatcher.find_template(tpl_img, conf, exclude_rect=exclude)
        if match:
            cx, cy, score = match
            pct = int(round(score * 100))
            if and_click:
                btn = self.engine.template_config.get("button", "left")
                smooth = self.engine.template_config.get("smooth_move", True)
                dur = self.engine.template_config.get("move_duration", 0.20)
                self.engine.play_sound("trigger")
                InputDriver.move_and_click(cx, cy, button=btn, hold_time=0.035, smooth=smooth, duration=dur)
                if self.engine.ripple_enabled and self.engine.on_ripple:
                    self.engine.on_ripple(cx, cy)
                self.test_status_label.configure(
                    text=f"🎯 Found & Clicked '{name}' at ({cx}, {cy}) | Match: {pct}%!",
                    text_color="#a6e3a1",
                )
            else:
                self.test_status_label.configure(
                    text=f"✓ Found '{name}' at ({cx}, {cy}) | Match: {pct}%",
                    text_color="#a6e3a1",
                )
        else:
            self.test_status_label.configure(
                text=f"✗ '{name}' was not found on screen (Threshold: {int(conf*100)}%). Make sure it is visible!",
                text_color="#f38ba8",
            )

    def _test_and_click_now(self):
        """Scans screen across all active targets and clicks the best match immediately."""
        self._test_search_now(and_click=True)

    def _test_search_now(self, and_click: bool = False):
        """Scans screen across all currently enabled targets."""
        active = [t for t in self.templates if t.get("enabled", True)]
        conf = float(self.conf_slider.get()) / 100.0

        if not active:
            # Fallback to single template_path if available
            t_path = self.engine.template_config.get("template_path", "")
            if t_path and os.path.exists(t_path):
                active = [{"name": os.path.basename(t_path), "path": t_path}]
            else:
                self.test_status_label.configure(
                    text="⚠️ No active targets selected! Paste or check a target first.",
                    text_color="#f9e2af",
                )
                return

        candidates = []
        for t in active:
            p = t.get("path", "")
            if p and os.path.exists(p):
                img = TemplateMatcher.load_template_file(p)
                if img is not None:
                    candidates.append((img, conf, t))

        if not candidates:
            self.test_status_label.configure(
                text="⚠️ None of the target image files could be loaded.",
                text_color="#f38ba8",
            )
            return

        exclude = None
        try:
            root = self.winfo_toplevel()
            if root and root.state() != "iconic":
                exclude = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height())
        except Exception:
            pass

        flow_mode = self.engine.template_config.get("flow_mode", "SEQUENCE")
        on_not_found = self.engine.template_config.get("on_not_found", "WAIT")
        btn = self.engine.template_config.get("button", "left")

        if flow_mode == "SEQUENCE" and len(candidates) > 1:
            if on_not_found == "WAIT":
                # Check Step #1 specifically
                first_cand = candidates[0]
                match = TemplateMatcher.find_any_template([first_cand], exclude_rect=exclude)
                meta = first_cand[2]
                name = meta.get("name", "Target #1")
                if match:
                    cx, cy, score, _ = match
                    pct = int(round(score * 100))
                    if and_click:
                        smooth = self.engine.template_config.get("smooth_move", True)
                        dur = self.engine.template_config.get("move_duration", 0.20)
                        self.engine.play_sound("trigger")
                        InputDriver.move_and_click(cx, cy, button=btn, hold_time=0.035, smooth=smooth, duration=dur)
                        if self.engine.ripple_enabled and self.engine.on_ripple:
                            self.engine.on_ripple(cx, cy)
                        self.test_status_label.configure(
                            text=f"🎯 [Step 1 of {len(candidates)}] Found & Clicked '{name}' at ({cx}, {cy})! Match: {pct}%",
                            text_color="#a6e3a1",
                        )
                    else:
                        self.test_status_label.configure(
                            text=f"✓ [Step 1 of {len(candidates)}] Found '{name}' at ({cx}, {cy}) | Match: {pct}%",
                            text_color="#a6e3a1",
                        )
                else:
                    self.test_status_label.configure(
                        text=f"⏳ Step 1 ('{name}') not currently visible on screen. In live mode, bot will wait for it before proceeding to Step 2.",
                        text_color="#f9e2af",
                    )
            else:
                # "Go to next if not found": scan in order and click first visible target
                found_match = None
                skipped_names = []
                for idx, cand in enumerate(candidates):
                    m = TemplateMatcher.find_any_template([cand], exclude_rect=exclude)
                    if m:
                        found_match = (m, idx, cand)
                        break
                    else:
                        skipped_names.append(cand[2].get("name", f"Target #{idx+1}"))

                if found_match:
                    (cx, cy, score, _), idx, cand = found_match
                    name = cand[2].get("name", f"Target #{idx+1}")
                    pct = int(round(score * 100))
                    skip_info = f" (Skipped: {', '.join(skipped_names)})" if skipped_names else ""
                    if and_click:
                        smooth = self.engine.template_config.get("smooth_move", True)
                        dur = self.engine.template_config.get("move_duration", 0.20)
                        self.engine.play_sound("trigger")
                        InputDriver.move_and_click(cx, cy, button=btn, hold_time=0.035, smooth=smooth, duration=dur)
                        if self.engine.ripple_enabled and self.engine.on_ripple:
                            self.engine.on_ripple(cx, cy)
                        self.test_status_label.configure(
                            text=f"🎯 [Step {idx+1} of {len(candidates)}] Clicked '{name}' at ({cx}, {cy})! Match: {pct}%{skip_info}",
                            text_color="#a6e3a1",
                        )
                    else:
                        self.test_status_label.configure(
                            text=f"✓ [Step {idx+1} of {len(candidates)}] Found '{name}' at ({cx}, {cy}) | Match: {pct}%{skip_info}",
                            text_color="#a6e3a1",
                        )
                else:
                    self.test_status_label.configure(
                        text=f"✗ None of the {len(candidates)} targets in queue were found on screen.",
                        text_color="#f38ba8",
                    )
        else:
            # flow_mode == "ANY" or single target: search all
            match = TemplateMatcher.find_any_template(candidates, exclude_rect=exclude)
            if match:
                cx, cy, score, meta = match
                name = meta.get("name", "Target")
                pct = int(round(score * 100))
                if and_click:
                    btn = self.engine.template_config.get("button", "left")
                    smooth = self.engine.template_config.get("smooth_move", True)
                    dur = self.engine.template_config.get("move_duration", 0.20)
                    self.engine.play_sound("trigger")
                    InputDriver.move_and_click(cx, cy, button=btn, hold_time=0.035, smooth=smooth, duration=dur)
                    if self.engine.ripple_enabled and self.engine.on_ripple:
                        self.engine.on_ripple(cx, cy)
                    self.test_status_label.configure(
                        text=f"🎯 Found & Clicked '{name}' at ({cx}, {cy})! Match: {pct}% (Active queue: {len(candidates)} targets)",
                        text_color="#a6e3a1",
                    )
                else:
                    self.test_status_label.configure(
                        text=f"✓ Match found! '{name}' at ({cx}, {cy}) | Confidence: {pct}% (Active queue: {len(candidates)} targets)",
                        text_color="#a6e3a1",
                    )
            else:
                self.test_status_label.configure(
                    text=f"✗ None of the {len(candidates)} active target(s) were found on screen (Threshold: {int(conf*100)}%).",
                    text_color="#f38ba8",
                )

    # =========================================================================
    # --- Precision & Settings Handlers ---
    # =========================================================================
    def _on_precision_mode_selected(self, choice: str):
        if "Exact" in choice:
            self._updating = True
            self.conf_slider.set(95)
            self._updating = False
            self._set_confidence_value(95, mode_name="Exact")
            self.precision_desc_label.configure(
                text="Exact (95%): Requires an almost pixel-perfect match. Zero false positives for crisp UI buttons & text.",
                text_color="#a6e3a1",
            )
        else:
            self._updating = True
            self.conf_slider.set(60)
            self._updating = False
            self._set_confidence_value(60, mode_name="Similar")
            self.precision_desc_label.configure(
                text="Similar (60%): Flexible matching for buttons with glowing, transparency, lighting, or animations.",
                text_color="#89b4fa",
            )

    def _set_confidence_value(self, pct: int, mode_name: Optional[str] = None):
        self.engine.template_config["confidence"] = pct / 100.0
        mode_str = mode_name or ("Exact" if pct >= 90 else "Similar")
        self.conf_val_label.configure(text=f"{pct}% ({mode_str})")

    def _on_conf_slider_changed(self, val):
        if self._updating:
            return
        pct = int(round(val))
        if pct >= 90:
            self.precision_seg.set("🎯 Exact (95%)")
            self._set_confidence_value(pct, "Exact")
        elif pct <= 65:
            self.precision_seg.set("🔍 Similar (60%)")
            self._set_confidence_value(pct, "Similar")
        else:
            self.precision_seg.set("")
            self._set_confidence_value(pct, "Custom")

    def _on_btn_changed(self, choice: str):
        # Extract base command: 'left', 'double', or 'right'
        raw = choice.split()[0].lower()
        self.engine.template_config["button"] = raw
        try:
            if raw == "double":
                self.test_click_btn.configure(text="🎯 Test & Double-Click")
            elif raw == "right":
                self.test_click_btn.configure(text="🎯 Test & Right-Click")
            else:
                self.test_click_btn.configure(text="🎯 Test & Click Target")
        except Exception:
            pass

    def _on_smooth_move_changed(self):
        enabled = bool(self.smooth_move_var.get())
        self.engine.template_config["smooth_move"] = enabled
        if enabled:
            self.move_speed_seg.configure(state="normal")
            self.travel_desc_lbl.configure(
                text='💡 Glides cursor over to icon naturally so Windows registers hover focus before clicking.',
                text_color="#a6e3a1",
            )
        else:
            self.move_speed_seg.configure(state="disabled")
            self.travel_desc_lbl.configure(
                text='⚡ Instant Jump: Cursor teleports directly to target coordinates.',
                text_color="#6c7086",
            )

    def _on_move_speed_changed(self, choice: str):
        if "Fast" in choice:
            self.engine.template_config["move_duration"] = 0.15
        elif "Gentle" in choice:
            self.engine.template_config["move_duration"] = 0.40
        else:
            self.engine.template_config["move_duration"] = 0.25

    def _on_cooldown_changed(self, event=None):
        try:
            cd = float(self.cooldown_entry.get().strip() or "0.5")
            self.engine.template_config["cooldown"] = max(0.05, cd)
        except ValueError:
            pass

    def _on_interval_changed(self, event=None):
        try:
            intv = float(self.interval_entry.get().strip() or "0.10")
            self.engine.template_config["search_interval"] = max(0.02, intv)
        except ValueError:
            pass

    def _on_flow_mode_changed(self, choice: str):
        if "Ordered" in choice:
            self.engine.template_config["flow_mode"] = "SEQUENCE"
            self.flow_behavior_lbl.configure(text_color="#cdd6f4")
            self.not_found_seg.configure(state="normal")
            self._update_flow_description()
        else:
            self.engine.template_config["flow_mode"] = "ANY"
            self.flow_desc_label.configure(
                text="⚡ Any Match: Searches for ALL active targets at once and clicks whatever matches first.",
                text_color="#89b4fa",
            )

    def _on_not_found_mode_changed(self, choice: str):
        if "Wait" in choice:
            self.engine.template_config["on_not_found"] = "WAIT"
        else:
            self.engine.template_config["on_not_found"] = "SKIP"
        self._update_flow_description()

    def _update_flow_description(self):
        flow = self.engine.template_config.get("flow_mode", "SEQUENCE")
        if flow == "ANY":
            self.flow_desc_label.configure(
                text="⚡ Any Match: Searches for ALL active targets at once and clicks whatever matches first.",
                text_color="#89b4fa",
            )
            return

        mode = self.engine.template_config.get("on_not_found", "WAIT")
        if mode == "WAIT":
            self.flow_desc_label.configure(
                text="⏳ Wait then Proceed: Waits until target appears on screen, clicks it, then moves to next step.",
                text_color="#a6e3a1",
            )
        else:
            self.flow_desc_label.configure(
                text="⏭️ Go to Next Target: If target is not currently visible on screen, skips it immediately and checks next step.",
                text_color="#fab387",
            )

    def _on_loop_queue_changed(self):
        self.engine.template_config["loop_queue"] = bool(self.loop_queue_var.get())

    def _toggle_bot_running(self):
        """Starts or stops the visual bot directly from this tab."""
        if not self.engine.is_running:
            self.engine.mode = self.engine.MODE_TEMPLATE
            self.engine.start()
        else:
            self.engine.stop()

    def sync_engine_state(self, is_running: bool):
        """Updates the Visual Bot tab Start/Stop button appearance."""
        try:
            if is_running and self.engine.mode == self.engine.MODE_TEMPLATE:
                self.start_stop_btn.configure(
                    text="⏹️ STOP VISUAL BOT [Win+*]",
                    fg_color="#f38ba8",
                    hover_color="#eba0ac",
                    text_color="#11111b",
                )
            else:
                self.start_stop_btn.configure(
                    text="▶️ START VISUAL BOT [Win+*]",
                    fg_color="#a6e3a1",
                    hover_color="#94e2d5",
                    text_color="#11111b",
                )
        except Exception:
            pass

    def _sync_from_config(self):
        cfg = self.engine.template_config
        conf = int(cfg.get("confidence", 0.60) * 100)
        self.conf_slider.set(conf)
        self._set_confidence_value(conf)

        if conf >= 90:
            self.precision_seg.set("🎯 Exact (95%)")
        else:
            self.precision_seg.set("🔍 Similar (60%)")

        btn = cfg.get("button", "double").lower()
        if "double" in btn:
            self.btn_selector.set("double (Double Click - Open App)")
        elif "right" in btn:
            self.btn_selector.set("right (Right Click)")
        else:
            self.btn_selector.set("left (Single Click)")
        self._on_btn_changed(self.btn_selector.get())

        smooth_val = cfg.get("smooth_move", True)
        self.smooth_move_var.set(smooth_val)
        dur = cfg.get("move_duration", 0.20)
        if dur <= 0.18:
            self.move_speed_seg.set("⚡ Fast (0.15s)")
        elif dur >= 0.35:
            self.move_speed_seg.set("🐢 Gentle (0.40s)")
        else:
            self.move_speed_seg.set("🎯 Smooth (0.25s)")
        self._on_smooth_move_changed()

        self.cooldown_entry.delete(0, "end")
        self.cooldown_entry.insert(0, str(cfg.get("cooldown", 0.5)))

        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(cfg.get("search_interval", 0.10)))

        # Sync Flow Mode & Missing Target Setting
        flow = cfg.get("flow_mode", "ANY")
        if flow == "SEQUENCE":
            self.flow_mode_seg.set("🔢 Ordered Steps (1➔2➔3)")
        else:
            self.flow_mode_seg.set("⚡ Any Match")

        on_not = cfg.get("on_not_found", "WAIT")
        if on_not == "WAIT":
            self.not_found_seg.set("⏳ Wait then Proceed")
        else:
            self.not_found_seg.set("⏭️ Go to Next Target")

        self._update_flow_description()
        self.loop_queue_var.set(cfg.get("loop_queue", True))

        # Load existing templates from config or scan assets/templates
        existing_templates = cfg.get("templates", [])
        if existing_templates:
            for t in existing_templates:
                p = t.get("path", "")
                if p and os.path.exists(p):
                    self._add_template_to_library(p, name=t.get("name"))
        else:
            # If assets/templates has existing files, populate only the single most recent one
            if os.path.exists(self.assets_dir):
                valid_exts = (".png", ".jpg", ".jpeg", ".bmp")
                files = sorted(
                    [
                        os.path.join(self.assets_dir, f)
                        for f in os.listdir(self.assets_dir)
                        if f.lower().endswith(valid_exts)
                    ],
                    key=os.path.getmtime,
                )
                if files:
                    self._add_template_to_library(files[-1])  # Only load the single most recent target

        self._refresh_queue_display()
