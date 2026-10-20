# ⚡ ApexClicker Pro v1.0.0 — Official Production Release

Welcome to the first official release of **ApexClicker Pro v1.0.0**, a next-generation Windows automation and anti-detection auto-clicking suite engineered for gamers, streamers, power users, and QA engineers.

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases/tag/v1.0.0)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Solf1re1/GhiLFm)

---

## 🚀 Key Highlights & Modules

### 1. ⚡ Ultra-Fast & Precision Burst Clicker
- **Sub-Millisecond Timing:** High-precision sleep scheduling capable of speeds from **0.1 CPS up to 1,000+ CPS**.
- **Mouse Action Support:** Left, Right, Middle click, and Double-Click.
- **Dynamic Targeting:** Click at live cursor location or pin to absolute coordinates with instant capture (`Ctrl + F8`).
- **Repeat Limits:** Set finite click counts or run indefinitely with zero drift.

### 2. 🎯 Multi-Point Path & Sequence Studio
- **Coordinate Waypoints:** Create rich multi-step routines with independent per-point delays, click types, and jitter radii.
- **Natural Bezier Gliding:** Optional smooth cursor interpolation between waypoints to mimic natural human hand movement.
- **Multi-Monitor Traversal:** Cross seamlessly across disparate DPI displays and monitor seams without cursor stutter or boundary entrapment.
- **Live Preview & Hotkey Capture:** Add points on the fly with a single keystroke.

### 3. 🛡️ Advanced Anti-Detection Humanizer Suite
- **Normal Distribution Jitter:** Gaussian-distributed randomized click intervals that defeat heuristic frequency analysis.
- **Micro-Displacement Drift:** Organic cursor jitter around target points (`±px` bounds) mimicking genuine muscle tremor.
- **Biometric Fatigue Simulation:** Gradually introduces micro-pauses and variable reaction intervals simulating human fatigue over extended sessions.
- **Configurable Anti-Cheat Profiles:** Tailored settings for competitive gaming (e.g. Minecraft PVP, Roblox, MMOs).

### 4. 👁️ Pixel & Color Reactive Trigger
- **Real-Time Screen Polling:** Continuously scans targeted pixel coordinates with sub-10ms responsiveness.
- **Tolerance & Color Distance:** Euclidean color distance threshold matching (0–100%) accommodating anti-aliasing and ambient game lighting.
- **Sampling Utility:** Sample any pixel on screen instantly with `Ctrl + F9`.

### 5. 🖼️ Visual Bot & Image Template Search
- **Dual Matching Engine:** Combines **Grayscale Normalized Cross-Correlation** (`TM_CCOEFF_NORMED`) with **Structural Edge Matching** (`Canny` contours) for glowing, animated, or semi-transparent targets (e.g., Discord UI icons, desktop shortcuts).
- **Clipboard Import:** Instant screenshot capture via `Win + Shift + S` or PrintScreen and direct import via `Paste from Clipboard` or `Ctrl + V`.
- **Confidence Control:** Adjustable similarity matching threshold (50%–99%) for exact or fuzzy visual recognition.
- **Multi-Target Storage:** Save and switch between visual templates on the fly.
- **Match Actions:** Move cursor, single click, or double click to automatically launch applications.

### 6. ⌨️ Keyboard Spammer & Key Presser
- **Any Key Support:** Alphanumeric, modifier keys, navigation, and function keys (`F1`–`F12`).
- **Hold or Burst:** Adjustable key hold duration and repeat delay down to milliseconds.

### 7. 🎬 Macro Recording Studio
- **Full Input Capture:** Record raw keyboard strokes, mouse clicks, movements, and pauses in real-time.
- **Precision Playback:** Play back recorded macros with adjustable playback speed multiplier (0.25x to 5.0x).

### 8. ⏱️ Automation Scheduler & Window Process Locking
- **Game / Process Locking:** Pin clicks to target foreground processes (e.g. `javaw.exe`, `RobloxPlayerBeta.exe`) so background clicks never misfire if you switch windows.
- **Auto-Stop Countdown:** Set automated run timers (Hours, Minutes, Seconds) with configurable completion actions:
  - Stop clicker only
  - Play audible alarm beeps
  - Suspend / Sleep PC
  - Shut down computer
- **Floating Mini-HUD:** Compact, translucent on-screen status overlay.

---

## ⌨️ Global Hotkeys Quick Reference

| Action | Primary Hotkey | Secondary / Global Alternative |
| :--- | :---: | :---: |
| **Start / Stop Auto Clicker** | `Ctrl + F6` | `Win + *` |
| **Pause / Resume** | `Ctrl + F7` | `Win + /` |
| **Capture Cursor Coordinates** | `Ctrl + F8` | UI Coordinate Picker |
| **Sample Screen Pixel Color** | `Ctrl + F9` | UI Pixel Eyedropper |
| **Toggle Macro Recording** | `Ctrl + F10` | UI Record / Stop |
| **Paste Image from Clipboard** | `Ctrl + V` | UI "Import Clipboard" Button |

> All hotkeys are customizable directly within the **⚙️ Settings & Safety** tab.

---

## 📦 Binaries Available in v1.0.0

Choose the edition that best fits your needs:

| Edition | File | Size | SHA-256 | Best For |
| :--- | :--- | :---: | :---: | :--- |
| **Slim Edition (< 25 MB)** | [`ApexClicker-Slim.exe`](dist/ApexClicker-Slim.exe) | **19.5 MB** | `E18D70854E6C5D10F87E02EB4E63DCD3545EA154563C76D9CCB5172AEE57B53A` | Direct GitHub web upload, lightweight, includes Burst, Sequences, Humanizer, Pixel Trigger, Key Spammer, and Macro Studio |
| **Full Pro Edition** | [`ApexClicker.exe`](dist/ApexClicker.exe) | **71.7 MB** | `14486EC4481E645838705F030BA75BFA122597160D614B6B22640FDB2252B06D` | Full standalone package with bundled OpenCV engine for Visual Bot template matching |

---

## 📥 Installation & How to Run

1. Download **`ApexClicker.exe`** from the [GitHub Releases Page](https://github.com/Solf1re1/GhiLFm/releases).
2. Save it anywhere on your PC (e.g., Desktop or `C:\Tools\ApexClicker`).
3. *(Optional)* Click **⚙️ Settings & Safety -> Create Desktop Shortcut** to place an official application shortcut on your Windows desktop.
4. Launch and enjoy!

---

## 🔄 Check for Updates

ApexClicker Pro v1.0.0 features built-in update checking directly linked to the official repository:
- **Repository:** [https://github.com/Solf1re1/GhiLFm](https://github.com/Solf1re1/GhiLFm)
- **Releases:** [https://github.com/Solf1re1/GhiLFm/releases](https://github.com/Solf1re1/GhiLFm/releases)
