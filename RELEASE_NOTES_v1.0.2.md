# ⚡ ApexClicker Pro v1.0.2 — Tab Navigation Fix & In-App Auto-Updater

ApexClicker Pro **v1.0.2** fixes tab loading across all secondary modules and introduces a seamless built-in **In-App Auto-Updater** with GitHub Releases integration and live progress tracking.

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.2-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases/tag/v1.0.2)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Solf1re1/GhiLFm)

---

## 🛠️ What's New & Fixed in v1.0.2

### 1. 🔄 Seamless In-App Auto-Updater
- **Silent Background Checks:** ApexClicker checks GitHub's Releases API in the background 3 seconds after boot without adding any latency to startup.
- **Manual "Check for Updates" Buttons:** Directly accessible from the header bar and the Settings & Safety tab.
- **One-Click Update & Restart:** Displays release notes, downloads the latest binary with a live progress bar, and automatically restarts into the new version via a detached background updater script.

### 2. 🎯 Fixed Tab Navigation & Full Module Bundling
- **Resolved Tab Loading Failure:** Fixed an issue where secondary tabs (Multi-Point Sequence, Anti-Detection, Pixel Trigger, Visual Bot, Key Spammer, Macro Studio, Settings) would not load in frozen builds.
- **Static Class Resolution & Lazy Instantiation:** All tab classes are now traced and statically bundled into the PyInstaller binary while retaining sub-second startup via deferred widget construction.
- **Automated Tab Switching Verification:** Added test coverage verifying that every tab loads and switches cleanly.

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

- **`ApexClicker-v1.0.2-Instant.zip`**: Pre-extracted instant-load distribution (~1-second boot time).
- **`ApexClicker.exe`**: Standalone single-file portable executable.
