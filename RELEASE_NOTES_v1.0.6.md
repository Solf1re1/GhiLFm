# Release Notes - ApexClicker Pro v1.0.6

### 🎬 Macro Studio & Hotkey Re-trigger Fixes
- **Ctrl+F10 Self-Triggering Eliminated:** Fixed a critical bug in Macro Studio where pressing `Ctrl+F10` to stop recording would accidentally capture the `Ctrl+F10` keystrokes into the macro file. When replaying the macro, the simulated keystrokes would trigger the global hotkey listener and start recording all over again.
- **Smart Hotkey Stripping & Sanitization:**
  - `MacroEngine` now actively filters out `F10` (and the trigger hotkey) during live recording so it is never saved to the event list.
  - Added an automatic sanitization pass that strips any initial modifier releases (fingers lifting off `Ctrl+F10` when starting) and trailing modifier presses (fingers pressing `Ctrl+F10` when stopping).
  - Existing macro files loaded via "📂 Load Macro" or played back are automatically sanitized to remove any stray `Ctrl+F10` keystrokes.
- **Playback Guard:**
  - Global hotkeys (`Ctrl+F10`) and `_toggle_recording` are strictly blocked while macro playback is active.
  - Added a 150ms post-playback buffer to prevent trailing OS keyboard input queue events from triggering new recordings.
  - Pressing `Ctrl+F7` (Pause) while a macro is playing safely halts playback.
