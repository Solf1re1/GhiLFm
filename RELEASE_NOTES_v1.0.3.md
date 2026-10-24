# ⚡ ApexClicker Pro v1.0.3 — In-App Updater Reliability Hotfix

ApexClicker Pro **v1.0.3** replaces the batch self-updater with a dedicated PowerShell updater engine that resolves Windows process lock issues and ensures seamless auto-updating and relaunching.

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.3-blue.svg)](https://github.com/Solf1re1/GhiLFm/releases/tag/v1.0.3)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Solf1re1/GhiLFm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/Solf1re1/GhiLFm)

---

## 🛠️ What's Fixed in v1.0.3

### 1. 🔄 Bulletproof In-App Self-Updating Engine
- **Windows Process Handle Resolution:** Fixed an issue in previous builds where the updater script failed to overwrite the `.exe` because the PyInstaller parent bootloader process was still holding a file lock.
- **Consoleless Execution Fix:** Replaced fragile `cmd.exe` batch execution with a robust background PowerShell updater. Fixed process creation flags (`CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`) so the updater never silently aborts without a console.
- **Atomic Rename-Then-Copy Fallback:** Implemented the industry-standard atomic rename pattern (`MoveFile` -> copy -> delete) allowing locked executables to be replaced instantly and cleanly.
- **Reliable Process Termination & Relaunch:** Ensures all instances of the application terminate before file replacement and guarantees automatic relaunching in the correct directory.

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
- **`ApexClicker-v1.0.3-Instant.zip`**: Pre-extracted instant-load distribution (~1-second boot time).
