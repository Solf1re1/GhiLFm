# ⚡ ApexClicker Pro v1.0.7 — PyInstaller Bootloader & In-App Restart Hotfix

### 🐛 Critical Fixes & Reliability Improvements
- **Resolved `_PYI_APPLICATION_HOME_DIR` Startup Crash:**
  - Fixed an issue where restarting the application via the built-in auto-updater caused PyInstaller's C bootloader to mistakenly believe the new instance was an internal worker subprocess inheriting from the parent process.
  - Added full environment scrubbing (`_PYI_*` flags) prior to updater execution and explicitly injected PyInstaller's official `PYINSTALLER_RESET_ENVIRONMENT=1` flag in the PowerShell relaunch pipeline.
- **Multiprocessing Freeze Support:**
  - Added `multiprocessing.freeze_support()` at the main application entry point to ensure frozen child processes initialize cleanly on Windows.
  - Added cleanup for `PYINSTALLER_RESET_ENVIRONMENT` in the application root loop.

### 📦 Available Assets
- `ApexClicker.exe`: Fully portable single-file executable (no installation required).
- `ApexClicker-v1.0.7-Instant.zip`: Pre-extracted instant-launch package for fast startup without temporary extraction delays.
