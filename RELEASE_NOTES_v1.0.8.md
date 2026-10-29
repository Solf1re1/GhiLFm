# ⚡ ApexClicker Pro v1.0.8 — Macro Studio Mode Arming & Hotkey Integration

### 🌟 What's New & Fixed
- **Macro Studio First-Class Mode Arming:**
  - Navigating to the **🎬 Macro Studio** tab now immediately arms Macro Studio mode, updating the header badge to `Mode: 🎬 Macro Studio`.
  - Pressing the master Start/Stop hotkey (`Ctrl + F6`) or clicking the sidebar **START / STOP** button while armed in Macro Studio directly starts and stops macro playback.
- **Universal Toggle Guard & Collision Prevention:**
  - Resolved the bug where pressing `Ctrl + F6` to stop macro playback inadvertently launched the previously selected clicker mode (e.g. Burst Clicker) at high CPS.
  - Implemented centralized execution arbitration (`_handle_master_toggle`):
    - If a macro is actively playing or recording, pressing `Ctrl + F6` stops the macro immediately and guarantees the clicker is never started.
    - If the clicker is running, starting a macro or recording automatically terminates the clicker first.
- **Dynamic Hotkey UI Sync:**
  - Macro Studio's **Play Macro** button now dynamically reflects the current master hotkey (`▶️ Play Macro [Ctrl+F6]` / `⏹️ Stop Playback [Ctrl+F6]`).
  - Macro Studio's **Record** button dynamically displays the record hotkey (`⏺️ Start Recording [Ctrl+F10]` / `⏹️ Stop Recording [Ctrl+F10]`).
- **State Synchronization:**
  - Macro playback state is now fully synchronized with the global status badge (`● RUNNING (MACRO)`), sidebar buttons, and the floating Mini HUD overlay.

### 📦 Available Assets
- `ApexClicker.exe`: Fully portable single-file executable.
- `ApexClicker-v1.0.8-Instant.zip`: Pre-extracted instant-launch package for fast startup.
