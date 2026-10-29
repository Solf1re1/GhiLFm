"""
ApexClicker Master UI Window.
Modern, rock-solid, fully responsive desktop interface with sidebar navigation,
dynamic multi-mode switching, and live performance monitoring.
"""

import os
import sys
import time
import queue
import webbrowser
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict

from apex_clicker import __version__
from apex_clicker.core.clicker_engine import ClickerEngine
from apex_clicker.core.macro_recorder import MacroEngine
from apex_clicker.core.hotkey_manager import HotkeyManager
from apex_clicker.core.input_driver import InputDriver

from apex_clicker.ui.tabs.burst_tab import BurstTab
from apex_clicker.ui.tabs.sequence_tab import SequenceTab
from apex_clicker.ui.tabs.humanizer_tab import HumanizerTab
from apex_clicker.ui.tabs.pixel_tab import PixelTab
from apex_clicker.ui.tabs.template_tab import TemplateTab
from apex_clicker.ui.tabs.key_spammer_tab import KeySpammerTab
from apex_clicker.ui.tabs.macro_tab import MacroTab
from apex_clicker.ui.tabs.settings_tab import SettingsTab
from apex_clicker.ui.components.hud_overlay import MiniHudOverlay


class LazyPageDict(dict):
    """Dictionary that lazily instantiates tab views on first access to maximize startup speed."""

    def __init__(self, factories):
        super().__init__()
        self.factories = factories

    def __getitem__(self, key):
        if not dict.__contains__(self, key):
            if key in self.factories:
                val = self.factories[key]()
                dict.__setitem__(self, key, val)
                return val
            raise KeyError(key)
        return dict.__getitem__(self, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return key in self.factories or dict.__contains__(self, key)

    def is_instantiated(self, key):
        return dict.__contains__(self, key)


class MainWindow(ctk.CTk):
    """Main Application Window with Sidebar Navigation."""

    def __init__(self):
        super().__init__()

        # Appearance & Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Set Windows AppUserModelID for dedicated taskbar icon & grouping
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("apexclicker.pro.v1")
        except Exception:
            pass

        self.title(f"ApexClicker Pro v{__version__}")
        self.geometry("960x650")
        self.minsize(820, 560)
        self.configure(fg_color="#0f0f17")

        # Window Icon
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        self.icon_path = os.path.join(base_dir, "assets", "icon.ico")
        if not os.path.exists(self.icon_path) and getattr(sys, "frozen", False):
            self.icon_path = os.path.join(os.path.dirname(sys.executable), "assets", "icon.ico")
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except Exception:
                pass

        # Core Engines
        self.engine = ClickerEngine()
        self.macro_engine = MacroEngine()
        self.macro_engine.add_state_listener(self._on_macro_state_change)
        self.hotkey_mgr = HotkeyManager()

        # Mini HUD
        self.hud_window: Optional[MiniHudOverlay] = None
        self._last_ui_update_time = 0.0

        # Thread-safe UI state bridge
        self._pending_total_clicks = 0
        self._pending_current_cps = 0.0
        self._status_queue: queue.SimpleQueue = queue.SimpleQueue()

        # Build Sidebar & Pages
        self._build_layout()

        # Dynamic screen exclusion for template matching so UI never self-matches
        def _get_window_rect():
            try:
                if self.state() != "iconic":
                    return (self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height())
            except Exception:
                pass
            return None
        self.engine.exclude_rect_getter = _get_window_rect

        # Connect Core Callbacks
        self.engine.on_status_change = self._on_engine_status_change
        self.engine.on_click_update = self._on_engine_click_update

        # Setup Global Hotkeys
        self._setup_hotkeys()

        # Start stats refresher
        self._poll_stats()

        # Keyboard shortcuts (e.g. Ctrl+V to paste screenshot into Visual Bot)
        self.bind("<Control-v>", self._on_paste_event)
        self.bind("<Control-V>", self._on_paste_event)

        # Default topmost window
        self.attributes("-topmost", True)

        # Check for updates silently in background 3 seconds after launch
        self.after(3000, self._silent_update_check)

        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        # Configure root grid: Column 0 = fixed sidebar, Column 1 = expanding content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        sidebar = ctk.CTkFrame(
            self,
            fg_color="#181825",
            corner_radius=0,
            border_width=0,
            width=220,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # App Brand Header
        brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=14, pady=(16, 8))

        brand_title_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        brand_title_row.pack(fill="x")

        ctk.CTkLabel(
            brand_title_row,
            text="⚡ ApexClicker",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#cdd6f4",
        ).pack(side="left")

        ctk.CTkLabel(
            brand_title_row,
            text=f"v{__version__}",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#89b4fa",
        ).pack(side="left", padx=(6, 0), pady=(3, 0))

        toggle_key = self.hotkey_mgr.get_hotkey_display("toggle")
        self.status_badge = ctk.CTkLabel(
            brand_frame,
            text=f"● STOPPED [{toggle_key}]",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#f38ba8",
        )
        self.status_badge.pack(anchor="w", pady=(2, 0))

        # Live Stats Card in Sidebar
        stats_card = ctk.CTkFrame(sidebar, fg_color="#1e1e2e", corner_radius=8)
        stats_card.pack(fill="x", padx=14, pady=6)
        stats_card.grid_columnconfigure((0, 1), weight=1)

        rate_box = ctk.CTkFrame(stats_card, fg_color="transparent")
        rate_box.grid(row=0, column=0, padx=6, pady=6)
        ctk.CTkLabel(rate_box, text="RATE", font=ctk.CTkFont(size=9, weight="bold"), text_color="#a6adc8").pack()
        self.cps_display = ctk.CTkLabel(
            rate_box,
            text="0 CPS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#89b4fa",
        )
        self.cps_display.pack()

        clicks_box = ctk.CTkFrame(stats_card, fg_color="transparent")
        clicks_box.grid(row=0, column=1, padx=6, pady=6)
        ctk.CTkLabel(clicks_box, text="CLICKS", font=ctk.CTkFont(size=9, weight="bold"), text_color="#a6adc8").pack()
        self.clicks_display = ctk.CTkLabel(
            clicks_box,
            text="0",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#cdd6f4",
        )
        self.clicks_display.pack()

        # Primary Control Buttons
        pause_key = self.hotkey_mgr.get_hotkey_display("pause")
        self.start_btn = ctk.CTkButton(
            sidebar,
            text=f"▶️ START [{toggle_key}]",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#a6e3a1",
            text_color="#11111b",
            hover_color="#94e2d5",
            height=36,
            command=self._on_start_clicked,
        )
        self.start_btn.pack(fill="x", padx=14, pady=(6, 4))

        self.pause_btn = ctk.CTkButton(
            sidebar,
            text=f"⏸️ Pause [{pause_key}]",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#313244",
            hover_color="#45475a",
            height=28,
            command=self._on_pause_clicked,
        )
        self.pause_btn.pack(fill="x", padx=14, pady=(0, 10))

        # Divider
        ctk.CTkFrame(sidebar, height=1, fg_color="#313244").pack(fill="x", padx=14, pady=(0, 8))

        # Navigation Label
        ctk.CTkLabel(
            sidebar,
            text="MODULES",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#6c7086",
        ).pack(anchor="w", padx=16, pady=(0, 4))

        # Navigation Buttons Container
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.nav_items = [
            ("burst", "⚡ Burst Clicker", "⚡ Burst Clicker"),
            ("sequence", "🎯 Multi-Point", "🎯 Multi-Point Sequence"),
            ("humanizer", "🛡️ Anti-Detection", "🛡️ Anti-Detection Suite"),
            ("pixel", "👁️ Pixel Trigger", "👁️ Pixel & Color Reactive Trigger"),
            ("template", "🖼️ Visual Bot", "🖼️ Visual Bot & Image Template Search"),
            ("keyspam", "⌨️ Key Spammer", "⌨️ Keyboard Auto-Presser"),
            ("macro", "🎬 Macro Studio", "🎬 Macro Recording Studio"),
            ("settings", "⚙️ Settings & Safety", "⚙️ Preferences, Window Lock & Safety"),
        ]

        for key, btn_text, page_title in self.nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=btn_text,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                anchor="w",
                fg_color="transparent",
                text_color="#cdd6f4",
                hover_color="#313244",
                height=32,
                corner_radius=6,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_buttons[key] = btn

        # ==================== MAIN CONTENT AREA ====================
        content_wrapper = ctk.CTkFrame(self, fg_color="#0f0f17", corner_radius=0)
        content_wrapper.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        content_wrapper.grid_rowconfigure(1, weight=1)
        content_wrapper.grid_columnconfigure(0, weight=1)

        # Content Header Banner
        header_banner = ctk.CTkFrame(content_wrapper, fg_color="#181825", corner_radius=0, height=48)
        header_banner.grid(row=0, column=0, sticky="ew")
        header_banner.pack_propagate(False)

        self.page_title_label = ctk.CTkLabel(
            header_banner,
            text="⚡ Burst Clicker",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#cdd6f4",
        )
        self.page_title_label.pack(side="left", padx=16, pady=10)

        self.armed_mode_label = ctk.CTkLabel(
            header_banner,
            text="Mode: ⚡ Burst Clicker",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#a6e3a1",
            fg_color="#1e1e2e",
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self.armed_mode_label.pack(side="left", padx=10, pady=10)

        github_btn = ctk.CTkButton(
            header_banner,
            text="🌐 Check for Updates",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#89b4fa",
            height=28,
            width=140,
            corner_radius=6,
            command=self._on_check_updates_clicked,
        )
        github_btn.pack(side="right", padx=16, pady=10)

        # Content Container (where tab views live)
        self.content_container = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Lazy-Loaded Tab Pages (only instantiates when clicked)
        self.pages = LazyPageDict({
            "burst": lambda: BurstTab(self.content_container, self.engine),
            "sequence": lambda: SequenceTab(self.content_container, self.engine),
            "humanizer": lambda: HumanizerTab(self.content_container, self.engine),
            "pixel": lambda: PixelTab(self.content_container, self.engine),
            "template": lambda: TemplateTab(self.content_container, self.engine),
            "keyspam": lambda: KeySpammerTab(self.content_container, self.engine),
            "macro": lambda: MacroTab(
                self.content_container,
                self.macro_engine,
                self.hotkey_mgr,
                on_toggle_playback=self._toggle_macro_playback,
            ),
            "settings": lambda: SettingsTab(
                self.content_container,
                self.engine,
                self.hotkey_mgr,
                on_toggle_hud=self._toggle_hud_visibility,
                on_toggle_topmost=self._toggle_topmost,
                on_profile_loaded=self._on_profile_loaded,
            ),
        })

        self.current_page_key = "burst"
        self.active_execution_mode = "burst"
        self.show_page("burst")

    def _update_armed_mode_display(self):
        """Updates header badge displaying the current operational engine mode."""
        mode_names = {
            self.engine.MODE_BURST: "⚡ Burst Clicker",
            self.engine.MODE_SEQUENCE: "🎯 Multi-Point Sequence",
            self.engine.MODE_PIXEL: "👁️ Pixel Trigger",
            self.engine.MODE_TEMPLATE: "🖼️ Visual Bot",
            self.engine.MODE_KEYSPAM: "⌨️ Key Spammer",
            "macro": "🎬 Macro Studio",
        }
        if getattr(self, "active_execution_mode", "") == "macro":
            name = "🎬 Macro Studio"
        else:
            name = mode_names.get(self.engine.mode, self.engine.mode)
        if hasattr(self, "armed_mode_label"):
            self.armed_mode_label.configure(text=f"Mode: {name}")

    def show_page(self, page_key: str):
        """Switches active page in the content area without breaking execution mode."""
        if page_key not in self.pages:
            return

        self.current_page_key = page_key

        # Update primary execution mode if user navigated to an execution tab
        execution_modes = {
            "burst": self.engine.MODE_BURST,
            "sequence": self.engine.MODE_SEQUENCE,
            "pixel": self.engine.MODE_PIXEL,
            "template": self.engine.MODE_TEMPLATE,
            "keyspam": self.engine.MODE_KEYSPAM,
            "macro": "macro",
        }
        if page_key in execution_modes:
            self.active_execution_mode = page_key
            if page_key != "macro":
                self.engine.mode = execution_modes[page_key]
        self._update_armed_mode_display()

        # Update sidebar button highlighting
        for k, btn in self.nav_buttons.items():
            if k == page_key:
                btn.configure(fg_color="#313244", text_color="#89b4fa", font=ctk.CTkFont(weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#cdd6f4", font=ctk.CTkFont(weight="normal"))

        # Update header banner title
        for k, _, title in self.nav_items:
            if k == page_key:
                self.page_title_label.configure(text=title)
                break

        # Display target page
        try:
            for p in self.pages.values():
                p.pack_forget()

            target_page = self.pages[page_key]
            # Synchronize state if tab supports sync
            if hasattr(target_page, "_sync_from_engine"):
                try:
                    target_page._sync_from_engine()
                except Exception:
                    pass
            target_page.pack(fill="both", expand=True)
        except Exception as e:
            print(f"Error loading tab '{page_key}': {e}")

    def _setup_hotkeys(self):
        """Binds system-wide global hotkeys with Hold vs Toggle support."""
        self.macro_engine.set_stop_hotkey(self.hotkey_mgr.bindings.get("macro_toggle", "ctrl+f10"))
        self.hotkey_mgr.set_callback("toggle", self._hotkey_toggle_press)
        self.hotkey_mgr.set_release_callback("toggle", self._hotkey_toggle_release)
        self.hotkey_mgr.set_callback("pause", self._hotkey_pause)
        self.hotkey_mgr.set_callback("pick_coord", self._hotkey_pick_coord)
        self.hotkey_mgr.set_callback("sample_pixel", self._hotkey_sample_pixel)
        self.hotkey_mgr.set_callback("macro_toggle", self._hotkey_macro_toggle)
        self.hotkey_mgr.start()

    def _activate_mode_from_page(self):
        """Maps active sidebar page to engine operational mode preserving non-execution modules."""
        execution_modes = {
            "burst": self.engine.MODE_BURST,
            "sequence": self.engine.MODE_SEQUENCE,
            "pixel": self.engine.MODE_PIXEL,
            "template": self.engine.MODE_TEMPLATE,
            "keyspam": self.engine.MODE_KEYSPAM,
            "macro": "macro",
        }
        if self.current_page_key in execution_modes:
            self.active_execution_mode = self.current_page_key
            if self.current_page_key != "macro":
                self.engine.mode = execution_modes[self.current_page_key]
        elif hasattr(self, "active_execution_mode") and self.active_execution_mode in execution_modes:
            if self.active_execution_mode != "macro":
                self.engine.mode = execution_modes[self.active_execution_mode]
        self._update_armed_mode_display()

    def _toggle_macro_playback(self):
        """Starts or stops macro playback from master hotkey or start button."""
        if self.macro_engine.is_playing:
            self.macro_engine.stop_playback()
            return

        if not self.macro_engine.events:
            macro_key = self.hotkey_mgr.get_hotkey_display("macro_toggle")
            self.status_badge.configure(text=f"● NO MACRO (Press {macro_key} to Record)", text_color="#f9e2af")
            return

        # Ensure ClickEngine is not running
        if self.engine.is_running:
            self.engine.stop()

        speed = 1.0
        loops = 1
        if self.pages.is_instantiated("macro"):
            macro_page = self.pages["macro"]
            try:
                speed = float(macro_page.speed_slider.get())
            except Exception:
                pass
            try:
                loops = int(macro_page.loop_entry.get().strip() or "1")
            except Exception:
                pass

        self.macro_engine.start_playback(speed_multiplier=speed, repeat_count=loops)

    def _handle_master_toggle(self):
        """Master execution toggle handling both ClickEngine and MacroEngine."""
        # 1. If macro is currently playing, ALWAYS stop it on toggle! Never start clicker!
        if self.macro_engine.is_playing:
            self.macro_engine.stop_playback()
            return

        # 2. If macro is currently recording, stop it! Never start clicker!
        if self.macro_engine.is_recording:
            self.macro_engine.stop_recording()
            return

        # 3. If clicker engine is currently running, stop it!
        if self.engine.is_running:
            self.engine.stop()
            return

        # 4. Neither is running -> Start the armed mode
        self._activate_mode_from_page()
        if self.active_execution_mode == "macro":
            self._toggle_macro_playback()
        else:
            self.engine.start()

    def _hotkey_toggle_press(self):
        if self.engine.hotkey_mode == "HOLD":
            if not self.engine.is_running and not self.macro_engine.is_playing:
                self._activate_mode_from_page()
                if self.active_execution_mode == "macro":
                    self._toggle_macro_playback()
                else:
                    self.engine.start()
        else:
            self._handle_master_toggle()

    def _hotkey_toggle_release(self):
        if self.engine.hotkey_mode == "HOLD":
            if self.macro_engine.is_playing:
                self.macro_engine.stop_playback()
            if self.engine.is_running:
                self.engine.stop()

    def _hotkey_pause(self):
        if self.macro_engine.is_playing:
            self.macro_engine.stop_playback()
            return
        self.engine.toggle_pause()

    def _hotkey_pick_coord(self):
        x, y = InputDriver.get_cursor_pos()
        if self.current_page_key == "sequence":
            self.after(0, lambda: self.pages["sequence"].add_current_cursor_point(x, y))
        else:
            self.after(0, lambda: self.pages["burst"].set_coordinate(x, y))

    def _hotkey_sample_pixel(self):
        self.after(0, self.pages["pixel"].sample_current_cursor)

    def _hotkey_macro_toggle(self):
        if self.macro_engine.is_playing:
            return
        if self.engine.is_running:
            self.engine.stop()
        self.after(0, self.pages["macro"]._toggle_recording)

    def _on_paste_event(self, event=None):
        focused = self.focus_get()
        if focused and isinstance(focused, (tk.Entry, ctk.CTkEntry)):
            return
        if self.current_page_key == "template":
            self.pages["template"]._import_from_clipboard()

    def _on_start_clicked(self):
        self._handle_master_toggle()

    def _on_pause_clicked(self):
        self._hotkey_pause()

    def _on_macro_state_change(self, is_recording: bool, is_playing: bool):
        self.after(0, lambda: self._apply_macro_state_change(is_recording, is_playing))

    def _apply_macro_state_change(self, is_recording: bool, is_playing: bool):
        toggle_key = self.hotkey_mgr.get_hotkey_display("toggle")
        macro_key = self.hotkey_mgr.get_hotkey_display("macro_toggle")
        if is_playing:
            self.status_badge.configure(text="● RUNNING (MACRO)", text_color="#a6e3a1")
            self.start_btn.configure(text=f"⏹️ STOP [{toggle_key}]", fg_color="#f38ba8", hover_color="#eba0ac")
            if self.hud_window:
                self.hud_window.update_stats(True, False, 0.0, len(self.macro_engine.events))
        elif is_recording:
            self.status_badge.configure(text=f"● RECORDING [{macro_key}]", text_color="#f38ba8")
            self.start_btn.configure(text=f"⏹️ STOP [{macro_key}]", fg_color="#f38ba8", hover_color="#eba0ac")
        else:
            if not self.engine.is_running:
                self.status_badge.configure(text=f"● STOPPED [{toggle_key}]", text_color="#f38ba8")
                self.start_btn.configure(text=f"▶️ START [{toggle_key}]", fg_color="#a6e3a1", hover_color="#94e2d5")
                if self.hud_window:
                    self.hud_window.update_stats(False, False, 0.0, self.engine.total_clicks)

    def _on_engine_status_change(self, is_running: bool, is_paused: bool, message: str):
        # Thread-safe dispatch via status queue
        self._status_queue.put((is_running, is_paused, message))

    def _apply_status_change(self, is_running: bool, is_paused: bool, message: str):
        """Applies engine state transitions to UI controls safely on the main Tkinter thread."""
        toggle_key = self.hotkey_mgr.get_hotkey_display("toggle")
        pause_key = self.hotkey_mgr.get_hotkey_display("pause")
        tpl_page = self.pages["template"] if self.pages.is_instantiated("template") else None

        if is_running:
            # If Visual Bot started and auto-minimize is enabled, minimize window to keep game screen clear
            if self.engine.mode == self.engine.MODE_TEMPLATE:
                if tpl_page and getattr(tpl_page, "auto_minimize_var", None) and tpl_page.auto_minimize_var.get():
                    self.iconify()

            if is_paused:
                self.status_badge.configure(text=f"● PAUSED [{pause_key}]", text_color="#f9e2af")
                self.pause_btn.configure(text=f"▶️ Resume [{pause_key}]", fg_color="#89b4fa")
            else:
                self.status_badge.configure(text=f"● RUNNING ({self.engine.mode})", text_color="#a6e3a1")
                self.pause_btn.configure(text=f"⏸️ Pause [{pause_key}]", fg_color="#313244")

            self.start_btn.configure(text=f"⏹️ STOP [{toggle_key}]", fg_color="#f38ba8", hover_color="#eba0ac")
        else:
            # Restore window if it was minimized
            if self.state() == "iconic":
                self.deiconify()
                self.lift()

            self.status_badge.configure(text=f"● STOPPED [{toggle_key}]", text_color="#f38ba8")
            self.start_btn.configure(text=f"▶️ START [{toggle_key}]", fg_color="#a6e3a1", hover_color="#94e2d5")
            self.pause_btn.configure(text=f"⏸️ Pause [{pause_key}]", fg_color="#313244")

        # Sync Visual Bot tab button state
        if tpl_page and hasattr(tpl_page, "sync_engine_state"):
            tpl_page.sync_engine_state(is_running)

        if self.hud_window:
            self.hud_window.update_stats(
                is_running, is_paused, self.engine.current_cps, self.engine.total_clicks
            )

    def _on_engine_click_update(self, total_clicks: int, current_cps: float):
        # Atomic thread-safe stats update polled by main thread loop
        self._pending_total_clicks = total_clicks
        self._pending_current_cps = current_cps

    def _poll_stats(self):
        """Main-thread polling loop handling UI updates, stats, and thread-safe queues at 30 FPS."""
        # 1. Process status changes on main thread
        while not self._status_queue.empty():
            try:
                is_running, is_paused, message = self._status_queue.get_nowait()
                self._apply_status_change(is_running, is_paused, message)
            except Exception:
                break

        # 2. Render click and CPS stats on main thread
        if self.engine.is_running:
            self.clicks_display.configure(text=f"{self._pending_total_clicks:,}")
            self.cps_display.configure(text=f"{int(round(self._pending_current_cps))} CPS")
            if self.hud_window:
                self.hud_window.update_stats(
                    True, self.engine.is_paused, self._pending_current_cps, self._pending_total_clicks
                )
        else:
            if self.engine.current_cps > 0:
                self.engine.current_cps = 0.0
                self.cps_display.configure(text="0 CPS")
                if self.hud_window:
                    self.hud_window.update_stats(False, False, 0.0, self.engine.total_clicks)

        self.after(33, self._poll_stats)

    def _toggle_hud_visibility(self, visible: bool):
        if visible:
            if not self.hud_window:
                self.hud_window = MiniHudOverlay(self)
            self.hud_window.deiconify()
        else:
            if self.hud_window:
                self.hud_window.withdraw()

    def _toggle_topmost(self, topmost: bool):
        self.attributes("-topmost", topmost)

    def _on_profile_loaded(self):
        if self.pages.is_instantiated("burst"):
            self.pages["burst"]._sync_from_config()
        if self.pages.is_instantiated("sequence"):
            self.pages["sequence"].points = self.engine.sequence_config.get("points", [])
            self.pages["sequence"]._refresh_points_list()
        if self.pages.is_instantiated("humanizer"):
            self.pages["humanizer"]._sync_from_config()
        if self.pages.is_instantiated("pixel"):
            self.pages["pixel"]._sync_from_config()
        if self.pages.is_instantiated("template"):
            self.pages["template"]._sync_from_config()
        if self.pages.is_instantiated("keyspam"):
            self.pages["keyspam"]._sync_from_config()

    def _on_close(self):
        self.engine.stop()
        self.macro_engine.stop_recording()
        self.macro_engine.stop_playback()
        self.hotkey_mgr.stop()
        self.destroy()

    def _on_check_updates_clicked(self):
        from apex_clicker.ui.components.update_dialog import check_and_prompt_update
        from apex_clicker import __version__
        check_and_prompt_update(self, __version__, silent_if_latest=False)

    def _silent_update_check(self):
        try:
            from apex_clicker.ui.components.update_dialog import check_and_prompt_update
            from apex_clicker import __version__
            check_and_prompt_update(self, __version__, silent_if_latest=True)
        except Exception:
            pass
