# Release Notes - ApexClicker Pro v1.0.5

### 🎯 Multi-Point Sequence & Anti-Detection Fixes
- **Exact Coordinate Targeting (Machine Precision):** Fixed an issue where Multi-Point Sequence mode would not click at the designated target points when Anti-Detection was turned OFF. The engine now uses instant 1:1 pixel snapping, disables lateral Bezier sway/jitter, yields 40ms for OS & target window hover/focus message dispatch, and re-asserts exact coordinates before firing solid clicks.
- **Independent Execution Mode Persistence:** Fixed a bug where opening auxiliary panels (e.g., "🛡️ Anti-Detection Suite", "⚙️ Settings & Safety", or "🎬 Macro Studio") would reset the engine's operational mode to `MODE_BURST`. The engine now preserves whichever execution module was armed (`Multi-Point`, `Burst`, `Pixel Trigger`, `Visual Bot`, `Key Spammer`).
- **Live Armed Mode Indicator:** Added a dedicated mode badge in the header banner showing the currently armed operational mode (e.g. `Mode: 🎯 Multi-Point Sequence`).
- **In-Tab Anti-Detection Toggle & Status:** Added a direct toggle for Anti-Detection vs Machine Precision directly inside the Multi-Point Sequence tab, complete with status indicators (`⚡ Machine Precision: Instant 1:1 Snap (Zero Sway)` vs `🛡️ Anti-Detection: ACTIVE`).
- **3-Second Countdown Coordinate Picker:** Added a `⏱️ Pick Point (3s Countdown)` button to the Multi-Point tab. Users can now click the button, move their mouse over any game or application window, hear countdown beeps, and have the coordinate sampled accurately without capturing the button itself.
- **Target Location Preview:** Added a `🎯 Test` button to each point in the sequence list so users can instantly preview where the cursor will move.
- **Accurate Hotkey Picking (`Ctrl+F8`):** Hotkey coordinate sampling now passes the exact cursor position at the moment of the keypress directly to `SequenceTab`.
