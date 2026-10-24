# ⚡ ApexClicker Pro v1.0.1 — Performance & Optimization Release

ApexClicker Pro **v1.0.1** brings dramatic speed, latency, and CPU optimizations across the entire application, reducing startup times from nearly a minute down to ~1 second, streamlining input throughput for 1,000+ CPS burst clicking, and updating system hotkeys.

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.1-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases/tag/v1.0.1)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Solf1re1/GhiLFm)

---

## ⚡ What's New & Optimized in v1.0.1

### 1. 🚀 Instant Startup (~1-Second Launch)
- **Lazy Tab Architecture:** Rather than eagerly building all 8 complex interface pages at startup, only the primary Burst Tab is initialized on launch. Secondary modules (Multi-Point Sequence, Anti-Detection, Pixel Trigger, Visual Bot, Key Spammer, Macro Studio, Settings) load on-demand the instant their sidebar buttons are clicked.
- **Deferred Computer Vision Imports:** The heavy OpenCV (`cv2`) and NumPy computer vision engines are deferred until Visual Bot is explicitly utilized, eliminating unnecessary initialization delay on launch.
- **Pre-Extracted Application Directory:** The `--onedir` standalone build eliminates PyInstaller's `%TEMP%` extraction and Windows Defender scanning delay, opening the app in **~1.1 seconds**.

### 2. ⚡ Ultra-Low Latency Input Driver (`SendInput`)
- **Preallocated Ctypes Buffers:** Reuses preallocated `INPUT` structures and constant size references for Windows `SendInput`, cutting Python memory allocator churn and garbage collection pressure in tight clicking loops.
- **Thread-Local Desktop Handle Caching:** Eliminates repeated `OpenWindowStationW` and `OpenDesktopW` system calls on every click, maximizing click throughput.

### 3. 🖥️ Silky-Smooth GUI & CPU Throttling
- **Micro-Throttled Stats Dispatch:** Throttles UI click count updates and sliding-window CPS calculations to 30 FPS. At 500–1,000 CPS, this eliminates thousands of redundant Tkinter queue events per second, dropping background CPU usage from ~12% down to < 1% during intense clicking.

### 4. 🎯 High-Speed Window & Process Lock Caching
- **PID Process Caching:** Caches process names by PID in `WindowLockManager`, eliminating repeated OS process handle enumerations.

### 5. ⌨️ Dedicated Exclusive Hotkey: `Ctrl + F6`
- **Strict Exclusivity:** Start / Stop auto-clicking is mapped to **`Ctrl + F6`**.
- **Collision Protection:** The hotkey manager automatically unbinds any other action if reassigned to the same key combination, guaranteeing zero hotkey conflicts.

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

## 📦 Download & Deployment

- **Pre-Extracted Instant-Load Directory:** Located at `C:\moddingtools\ApexClicker\ApexClicker.exe` (Launches in ~1s).
- **Single-File Portable Binary:** Located at `C:\moddingtools\ApexClicker.exe` / `dist\ApexClicker.exe`.
- **GitHub Repository:** [https://github.com/Solf1re1/GhiLFm](https://github.com/Solf1re1/GhiLFm)
