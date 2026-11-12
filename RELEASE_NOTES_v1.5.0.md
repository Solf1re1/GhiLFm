# ApexClicker Pro v1.5.0 — Native .NET 9 Engine, Visual Bot Upgrade, Compact Overlay & Themes

### ⚡ What's New in v1.5.0

- **Visual Bot Overhaul & Smart Detection**:
  - **Two-Pass Global Template Search**: Fixed coordinate locking at $(0, 0)$ by evaluating global minimum error across the search region with fine $\pm 2$ local neighborhood refinement.
  - **Target Selection Strategy**: Added **🎯 Highest Confidence (Best Match)** vs **📍 Closest to Cursor (Nearest Match)** for prioritizing targets near the player/mouse.
  - **Precision Quick-Select**: Added **🎯 Exact (95%)**, **🔍 Similar (60%)**, and **✨ Closest (45%)** one-click sensitivity modes.
  - **Visual Search Area Box & Screen Drag-Picker**: Non-intrusive translucent bounding box (`SearchAreaWindow`) and fullscreen drag-selection tool (`RegionPickerWindow`) to visually preview and define screen search regions.
  - **Decimal Seconds Scan Interval**: Changed scan interval unit to seconds (e.g. `0.10s`), with full config persistence in `settings.json` and preset files.
  - **Visual Bot Profiles & Presets**: Save and load multi-target queues and settings under `profiles/visual_bot/`.

- **Pure Native .NET 9 Ultra-Fast Engine**:
  - Re-architected in high-performance C# / WPF.
  - Reduced executable footprint from 75 MB down to ~3.2 MB (single-file portable, instant startup).
  - High-precision microsecond spin-wait timer achieving rock-solid 1 to 1,000+ CPS without CPU throttling.

- **Universal Input Injection Fix (`mouse_event`)**:
  - Replaced Win32 `SendInput` with `mouse_event` to bypass Windows UIPI (`ERROR_ACCESS_DENIED`) restrictions.
  - Fully compatible with games running as Administrator, full-screen exclusive titles (Roblox, Minecraft, shooters), and web browsers.
  - Microsecond down-hold simulation guarantees every click registers across physical and virtual framebuffers.

- **Compact Mini-Overlay Mode**:
  - Instant toggle with `Ctrl + M` or the overlay button.
  - Floating, non-intrusive HUD with live CPS gauge, total click counter, and one-click play/pause.

- **UI & Theme Engine Refinements**:
  - **Theme Selector**: Instant theme switching: **Obsidian**, **Onyx (True Black)**, **Catppuccin Mocha**, and **Cyberpunk Neon**.
  - **Custom Dark Controls**: ComboBoxes and scrollbars now follow theme palettes, eliminating white dropdown boxes and out-of-place light scrollbars.
  - **Radio Button Grouping**: Added `BurstTargetMode` group name so "Follow Active Mouse Cursor" and "Fixed Coordinate" properly switch back and forth.
  - **Modular Streamlining**: Cleaned up the active module sidebar for 1.5.
