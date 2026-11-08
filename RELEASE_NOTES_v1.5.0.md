# ApexClicker Pro v1.5.0 — Native .NET 9 Engine, Compact Overlay & Multi-Theme System

### ⚡ What's New in v1.5.0

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

- **Theme Engine & Module Manager**:
  - Instant theme switching: **Obsidian**, **Onyx (True Black)**, **Catppuccin Mocha**, and **Cyberpunk Neon**.
  - Component selector: Toggle visible modules in the sidebar for a clean, distraction-free interface.
  - Fixed Aero dropdowns with custom dark ComboBox styling.

- **v2.0 Automation Studio Preview**:
  - Dedicated tab previewing the upcoming visual workflow automation pipeline.
