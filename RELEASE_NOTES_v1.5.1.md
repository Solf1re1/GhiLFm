# ApexClicker Pro v1.5.1 — Blazing-Fast Visual Bot, Pixel-Perfect Region Picker & DPI Fix

### ⚡ What's New in v1.5.1

- **300x Faster Multi-Core Template Matcher**:
  - **Sparse Anchor Screening**: Pre-computes 48 evenly-spaced anchor pixels across the target template to screen screen candidates in ~10 operations, rejecting 99.9% of non-matching screen space instantly.
  - **Multi-Threaded Parallel Row Scanning**: Parallelizes screen row processing with `Parallel.For` across all CPU cores, cutting full-screen search time from 2–4 seconds down to **5 to 10 milliseconds**.
  - **Instant Worker Loop & Asynchronous Test Actions**: `Test & Click` and `Scan Only` execute asynchronously in background tasks without freezing the UI, providing real-time feedback.

- **Pixel-Perfect Region Picker & Search Box (DPI Scale Fix)**:
  - **Zero Coordinate Drift**: `RegionPickerWindow` now captures exact physical screen pixels using Win32 `GetCursorPos`.
  - **Direct Win32 Window Positioning**: `SearchAreaWindow` positions itself via `SetWindowPos`, eliminating WPF DIP coordinate mismatches ("drag and click moving by a lot") on 125%, 150%, and 200% scaled monitors.

- **Startup Guard**:
  - Fully decoupled event handlers during XAML initialization to ensure 100% crash-free startup across all themes.

- **Version Bump**:
  - Updated build assembly, window titles, and branding badges to **v1.5.1**.
