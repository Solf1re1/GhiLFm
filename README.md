# ⚡ ApexClicker Pro • Advanced Automation & Anti-Detection Suite (v1.0.3)

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.3-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Solf1re1%2FGhiLFm-181717.svg?logo=github)](https://github.com/Solf1re1/GhiLFm)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)

ApexClicker Pro is a modern, high-performance desktop auto-clicker engineered for Windows with sub-millisecond precision, native Win32 `SendInput` simulation, intelligent anti-detection algorithms, real-time pixel triggers, dual-engine visual template matching, a full macro recording studio, and built-in seamless in-app auto-updating.

---

## 📥 Download Standalone Executable

No Python or external libraries required:
- **Download Executable:** [ApexClicker.exe (v1.0.3 Releases)](https://github.com/Solf1re1/GhiLFm/releases)

---

## 🌟 Key Features

### 1. ⚡ Extreme Burst & Precision Clicker
- **Sub-millisecond Timing:** Harnesses Windows Multimedia Timers (`timeBeginPeriod(1)`) to eliminate the 15.6ms OS quantum limit, achieving accurate **100 to 1,000+ Clicks Per Second (CPS)**.
- **Multiple Actions:** Left Click, Right Click, Middle Click, Double Click, Triple Click, Mouse Wheel Up/Down, and Hold mode.
- **Dynamic or Fixed Targeting:** Follow your active cursor in real-time or lock onto fixed screen coordinates with instant hotkey picking (`Ctrl+F8`).
- **Repeat Limits:** Run indefinitely or halt automatically after $N$ clicks.

### 2. 🎯 Multi-Point Sequence Clicker
- Chain multiple target coordinates in sequence.
- Configure independent delays, button actions, jitter radius, and smooth movements per step.
- Fast hotkey capture: press `Ctrl+F8` anywhere to add your current cursor coordinates into the sequence.
- Loop options: loop indefinitely or run $N$ cycles.

### 3. 🛡️ Anti-Detection & Human Simulation Suite
- **Natural Cubic Bezier Trajectories:** Replaces robotic teleports with biological acceleration/deceleration curves and natural sway.
- **Spatial Coordinate Jitter:** Applies 2D Gaussian clustering to disperse clicks organically within a custom radius.
- **Temporal Variance:** Randomizes delay intervals (e.g., $\pm20\%$) to defeat fixed-frequency anti-cheat heuristics.
- **Fatigue Micro-Pauses:** Periodically inserts natural muscle hesitation pauses (150–350ms) every 50–100 clicks.

### 4. 👁️ Pixel & Color Reactive Trigger
- **Zero-Lag Sampling:** Queries screen pixels at up to 10,000+ checks/sec via Win32 GDI.
- **Perceptual Color Distance:** Uses weighted Euclidean distance for accurate color matching.
- **Trigger Conditions:** Trigger when screen color **Matches** or **Changes/Differs**.
- **Eyedropper:** Press `Ctrl+F9` anywhere on screen to sample coordinates and color instantly with live swatch preview.

### 5. 🖼️ Visual Bot & Image Template Search
- **OpenCV Pattern Recognition:** Finds target UI buttons, icons, or visual game elements across the primary monitor.
- **Adjustable Confidence:** Set strictness threshold from 50% to 99% with instant live screen testing.
- **Auto-Center Clicking:** Calculates exact center bounding box coordinates to trigger clicks reliably.

### 6. ⌨️ Keyboard Auto-Presser & Key Spammer
- **Multi-Key Spammer:** Press single keys or rotations (e.g. `e`, `1, 2, 3, 4`, `space`).
- **Flexible Modes:** Simultaneous tapping, sequential cycling, or continuous holding.
- **Speed & Jitter:** 1 to 50 key presses/sec with human delay variance.

### 7. 🎬 Macro Recording Studio
- Record live mouse clicks, movements, scrolls, and keyboard keystrokes.
- Replay with variable speed multipliers (0.25x up to 4.0x) and loop settings.
- Export and import macro sequences as reusable JSON files.

### 8. 🎯 Process & Window Lock (Auto-Pause Safety)
- Bind clicking to a specific game or window (e.g. `RobloxPlayerBeta.exe`, `Minecraft.exe`, or browser).
- Automatically pauses the moment you switch windows or Alt-Tab, eliminating unwanted clicks on your desktop or Discord.

### 9. 🕹️ Hold-to-Click vs Toggle Modes
- **Toggle Mode:** Press once to start, press again to stop.
- **Hold-to-Click Mode:** Active only *while* holding down the hotkey, immediately halting the millisecond you release it.

### 10. ⏱️ Scheduled Timers & PC Sleep/Shutdown
- Set duration limits (Hours, Minutes, Seconds) with real-time countdown.
- Trigger actions on finish: audible alarms, automatic Windows sleep, or clean PC shutdown.

### 11. ✨ Click Ripple Visualizer & Floating Mini-HUD
- **Animated Click Ripples:** Transparent, click-through overlay showing pulsing ripple rings on every click.
- **Floating Mini-HUD:** Frameless, draggable, semi-transparent HUD overlay displaying real-time CPS, click count, and status without obscuring games or windows.
- System-wide global hotkeys that function even when the app is minimized or backgrounded:
  - `Win+*`: Quick Launch / Bring to Front ApexClicker Pro (via AutoHotkey: Numpad `*` or `Win+Shift+8`)
  - `Ctrl+F6`: Start / Stop Auto Clicker
  - `Ctrl+F7`: Pause / Resume Auto Clicker
  - `Ctrl+F8`: Capture Cursor Coordinate
  - `Ctrl+F9`: Sample Pixel Color Under Cursor
  - `Ctrl+F10`: Toggle Macro Recording

---

## 🚀 Quick Start

### Prerequisites
- Windows 10 / 11
- Python 3.10+ (Tested on Python 3.14)

### Running the App
Double-click `run_apex_clicker.bat` or run in terminal:
```powershell
python main.py
```

---

## 📁 Project Architecture

```
apex_clicker/
├── core/
│   ├── input_driver.py     # Native Win32 SendInput & 1ms Multimedia Timer
│   ├── humanizer.py        # Bezier curves, Gaussian jitter & fatigue
│   ├── clicker_engine.py   # Multi-threaded worker orchestrating all modes
│   ├── pixel_detector.py   # GDI pixel sampler & Delta-E matcher
│   ├── macro_recorder.py   # Mouse/keyboard input recorder and replayer
│   ├── hotkey_manager.py   # Global background hotkey dispatcher
│   └── profile_manager.py  # Preset & JSON profile loader/saver
├── profiles/               # Built-in and user-saved presets
├── ui/
│   ├── main_window.py      # Master dark-themed CustomTkinter UI
│   ├── components/
│   │   ├── hud_overlay.py  # Floating draggable Mini-HUD widget
│   │   └── coordinate_picker.py
│   └── tabs/
│       ├── burst_tab.py    # Extreme CPS & interval controls
│       ├── sequence_tab.py # Multi-point sequence editor
│       ├── humanizer_tab.py# Anti-detection suite controls
│       ├── pixel_tab.py    # Pixel color reactive triggers
│       ├── macro_tab.py    # Macro studio & playback
│       └── settings_tab.py # Hotkeys & profile presets
├── main.py                 # Application entry point
├── create_shortcut.py      # Desktop shortcut generator
├── requirements.txt        # Dependencies
├── run_apex_clicker.bat    # Windows batch launcher
├── assets/
│   ├── icon.ico            # Multi-size Windows application icon
│   └── icon.png            # High-res master icon (256x256)
└── scripts/
    └── generate_icon.py    # Icon generator script
```
