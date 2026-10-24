"""
In-App Update Dialog for ApexClicker Pro.
Provides a modern CustomTkinter modal popup displaying release notes,
live download progress bar, and one-click seamless update & restart.
"""

import os
import sys
import tempfile
import threading
import time
import webbrowser
import customtkinter as ctk
from typing import Optional, Dict, Any, Callable

from apex_clicker.core.updater import AppUpdater


class UpdateDialog(ctk.CTkToplevel):
    """Modal dialog for reviewing and applying application updates."""

    def __init__(self, master, current_version: str, release_info: Dict[str, Any]):
        super().__init__(master)

        self.master = master
        self.current_version = current_version
        self.release_info = release_info
        self.cancel_event = threading.Event()
        self.download_thread: Optional[threading.Thread] = None

        self.title("ApexClicker Pro — Update Available")
        self.geometry("540x480")
        self.minsize(480, 420)
        self.configure(fg_color="#0f0f17")

        # Keep on top of main window
        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._center_window()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self):
        self.update_idletasks()
        try:
            w = self.winfo_width()
            h = self.winfo_height()
            mx = self.master.winfo_x()
            my = self.master.winfo_y()
            mw = self.master.winfo_width()
            mh = self.master.winfo_height()
            x = mx + (mw - w) // 2
            y = my + (mh - h) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Frame
        header = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="🚀 New Version Available!",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color="#a6e3a1",
        ).pack(anchor="w", padx=16, pady=(12, 2))

        latest_tag = self.release_info.get("tag_name", "Latest")
        version_sub = f"Current: v{self.current_version}   ➔   Latest: {latest_tag}"
        ctk.CTkLabel(
            header,
            text=version_sub,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#89b4fa",
        ).pack(anchor="w", padx=16, pady=(0, 4))

        title = self.release_info.get("title", "")
        if title and title != latest_tag:
            ctk.CTkLabel(
                header,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#cdd6f4",
            ).pack(anchor="w", padx=16, pady=(0, 10))

        # Release Notes Title
        ctk.CTkLabel(
            self,
            text="What's New in This Release:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#a6adc8",
        ).grid(row=1, column=0, padx=20, pady=(4, 2), sticky="w")

        # Scrollable Release Notes
        notes_frame = ctk.CTkFrame(self, fg_color="#181825", corner_radius=8, border_width=1, border_color="#313244")
        notes_frame.grid(row=2, column=0, padx=16, pady=4, sticky="nsew")
        notes_frame.grid_columnconfigure(0, weight=1)
        notes_frame.grid_rowconfigure(0, weight=1)

        self.notes_text = ctk.CTkTextbox(
            notes_frame,
            fg_color="transparent",
            text_color="#cdd6f4",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            wrap="word",
        )
        self.notes_text.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        body = self.release_info.get("body", "No release notes provided.")
        self.notes_text.insert("1.0", body)
        self.notes_text.configure(state="disabled")

        # Download / Progress Area
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, padx=16, pady=6, sticky="ew")

        size_mb = self.release_info.get("size", 0) / (1024 * 1024)
        asset_name = self.release_info.get("asset_name", "ApexClicker.exe")
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Package: {asset_name} ({size_mb:.1f} MB)" if size_mb > 0 else f"Package: {asset_name}",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
        )
        self.status_label.pack(anchor="w", pady=(0, 4))

        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            fg_color="#313244",
            progress_color="#89b4fa",
            height=10,
        )
        self.progress_bar.pack(fill="x", pady=2)
        self.progress_bar.set(0)

        # Buttons Row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=4, column=0, padx=16, pady=(6, 16), sticky="ew")

        self.view_btn = ctk.CTkButton(
            btn_row,
            text="🌐 View on GitHub",
            font=ctk.CTkFont(size=11),
            fg_color="#313244",
            hover_color="#45475a",
            width=130,
            command=self._open_github,
        )
        self.view_btn.pack(side="left")

        self.cancel_btn = ctk.CTkButton(
            btn_row,
            text="Later",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color="#45475a",
            hover_color="#313244",
            width=80,
            command=self._on_close,
        )
        self.cancel_btn.pack(side="right", padx=(8, 0))

        self.update_btn = ctk.CTkButton(
            btn_row,
            text="⚡ Update & Restart Now",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#a6e3a1",
            text_color="#11111b",
            hover_color="#94e2d5",
            height=32,
            command=self._start_update,
        )
        self.update_btn.pack(side="right")

    def _open_github(self):
        url = self.release_info.get("html_url", "https://github.com/Solf1re1/GhiLFm/releases")
        webbrowser.open_new_tab(url)

    def _start_update(self):
        download_url = self.release_info.get("download_url")
        if not download_url:
            self.status_label.configure(
                text="Direct download binary not found. Please download from GitHub.",
                text_color="#f38ba8",
            )
            return

        self.update_btn.configure(state="disabled", text="Downloading...")
        self.cancel_btn.configure(text="Cancel")

        self.download_thread = threading.Thread(
            target=self._run_download,
            args=(download_url,),
            daemon=True,
        )
        self.download_thread.start()

    def _run_download(self, download_url: str):
        temp_dir = tempfile.gettempdir()
        temp_binary = os.path.join(temp_dir, f"ApexClicker_Update_{int(time.time())}.exe")

        def _on_progress(fraction: float, downloaded: int, total: int):
            if self.cancel_event.is_set():
                return
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            pct = int(fraction * 100)

            def _update_ui():
                try:
                    self.progress_bar.set(fraction)
                    self.status_label.configure(
                        text=f"Downloading update: {pct}% ({mb_down:.1f} MB / {mb_total:.1f} MB)...",
                        text_color="#89b4fa",
                    )
                except Exception:
                    pass

            self.after(0, _update_ui)

        success = AppUpdater.download_asset(
            download_url,
            temp_binary,
            progress_callback=_on_progress,
            cancel_event=self.cancel_event,
        )

        if self.cancel_event.is_set():
            return

        if success:
            def _success_ui():
                try:
                    self.status_label.configure(
                        text="✅ Download complete! Restarting to apply update...",
                        text_color="#a6e3a1",
                    )
                    self.progress_bar.set(1.0)
                    self.after(1000, lambda: AppUpdater.apply_update_and_restart(temp_binary))
                except Exception:
                    pass

            self.after(0, _success_ui)
        else:
            def _fail_ui():
                try:
                    self.status_label.configure(
                        text="❌ Download failed or was interrupted. Try again or view on GitHub.",
                        text_color="#f38ba8",
                    )
                    self.update_btn.configure(state="normal", text="Retry Update")
                except Exception:
                    pass

            self.after(0, _fail_ui)

    def _on_close(self):
        self.cancel_event.set()
        self.grab_release()
        self.destroy()


def show_up_to_date_dialog(master, current_version: str):
    """Shows a dialog informing the user that they are on the latest version."""
    dlg = ctk.CTkToplevel(master)
    dlg.title("ApexClicker Pro — Up to Date")
    dlg.geometry("380x200")
    dlg.minsize(360, 180)
    dlg.configure(fg_color="#0f0f17")
    dlg.transient(master)
    dlg.grab_set()

    # Center dialog
    dlg.update_idletasks()
    try:
        w, h = dlg.winfo_width(), dlg.winfo_height()
        x = master.winfo_x() + (master.winfo_width() - w) // 2
        y = master.winfo_y() + (master.winfo_height() - h) // 2
        dlg.geometry(f"+{max(0, x)}+{max(0, y)}")
    except Exception:
        pass

    content = ctk.CTkFrame(dlg, fg_color="#181825", corner_radius=10, border_width=1, border_color="#313244")
    content.pack(fill="both", expand=True, padx=16, pady=16)

    ctk.CTkLabel(
        content,
        text="✅ You're All Up to Date!",
        font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        text_color="#a6e3a1",
    ).pack(pady=(18, 4))

    ctk.CTkLabel(
        content,
        text=f"ApexClicker Pro v{current_version} is currently the latest version.",
        font=ctk.CTkFont(size=11),
        text_color="#cdd6f4",
    ).pack(pady=(0, 14))

    ctk.CTkButton(
        content,
        text="Close",
        font=ctk.CTkFont(size=11, weight="bold"),
        fg_color="#313244",
        hover_color="#45475a",
        width=100,
        height=28,
        command=dlg.destroy,
    ).pack(pady=(0, 10))


def check_and_prompt_update(master, current_version: str, silent_if_latest: bool = False):
    """
    Checks GitHub for updates in a background thread.
    If an update is found, presents the UpdateDialog.
    If up to date and not silent, presents the UpToDate dialog.
    """
    def _worker():
        release_info = AppUpdater.check_for_update(current_version)
        if release_info:
            master.after(0, lambda: UpdateDialog(master, current_version, release_info))
        elif not silent_if_latest:
            master.after(0, lambda: show_up_to_date_dialog(master, current_version))

    threading.Thread(target=_worker, daemon=True).start()
