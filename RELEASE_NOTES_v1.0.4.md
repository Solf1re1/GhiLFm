# ⚡ ApexClicker Pro v1.0.4 — Click Execution & Thread-Safe UI Hotfix

ApexClicker Pro **v1.0.4** fixes an immediate auto-stopping issue when starting the clicker and implements a thread-safe UI rendering architecture.

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.4-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases/tag/v1.0.4)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Solf1re1/GhiLFm)

---

## 🛠️ What's Fixed in v1.0.4

### 1. ⚡ Resolved Immediate Auto-Stop on Start
- **Import Error Resolution:** Fixed a missing `import time` dependency in `main_window.py` that caused the worker thread to encounter an unhandled `NameError` during the very first click calculation, which immediately halted the clicker.
- **Worker Thread Crash Protection:** Added protective exception barriers inside `_burst_worker`, `_sequence_worker`, and `_execute_click` ensuring background worker threads remain stable.

### 2. 🛡️ Thread-Safe Main Loop Architecture
- **Eliminated Cross-Thread Tkinter Calls:** Replaced cross-thread `widget.after(0, ...)` calls with atomic state polling and a thread-safe queue processed strictly on Tkinter's main event loop at 30 FPS.
- **Silky Smooth 30 FPS Rendering:** Prevents Tkinter main loop contention and guarantees stable UI responsiveness even during extreme 1,000+ CPS bursts.

---

## ⌨️ Default Hotkeys Quick Reference

| Action | Primary Hotkey |
| :--- | :---: |
| **Start / Stop Auto Clicker** | **`Ctrl + F6`** |
| **Pause / Resume** | **`Ctrl + F7`** |
| **Capture Cursor Coordinates** | **`Ctrl + F8`** |
| **Sample Screen Pixel Color** | **`Ctrl + F9`** |
| **Toggle Macro Recording** | **`Ctrl + F10`** |
| **Quick-Launch / Activate App (AHK)** | **`Win + *`** |

---

## 📦 Downloads & Binaries

- **`ApexClicker.exe`**: Standalone single-file portable executable.
- **`ApexClicker-v1.0.4-Instant.zip`**: Pre-extracted instant-load distribution (~1-second boot time).
