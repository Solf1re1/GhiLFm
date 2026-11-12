# ApexClicker Pro v1.5.3 — Pixel-Perfect Visual Bot, Native OCR & Universal Persistence

We are excited to release **ApexClicker Pro v1.5.3**, resolving template offset inaccuracies, candidate saturation on dark backgrounds, startup initialization errors, and introducing native Windows OCR support in Ordered Steps, custom preset naming, and universal settings persistence!

---

## 🌟 What's New & Fixed in v1.5.3

### 1. 🎯 Pixel-Perfect Feature-Weighted Template Matching
- **Resolved Dark Background False Matching & Drift**: Buttons (e.g. Nexus Mods "Slow download") typically consist of ~85% dark grey background with ~15% white text. In previous builds, unweighted comparisons allowed blank dark webpage regions to score 85-95% confidence, saturating candidate queues and causing the bot to click empty space below or above the button.
- **Contrast Feature Extraction**: The matching engine now computes the template's background color histogram and extracts high-contrast feature pixels (text characters, icons, borders).
- **Multi-Level Coarse-to-Fine Screening**:
  - Level 1: 32 feature anchors distributed across text and shapes (rejects blank areas in under 1 ms).
  - Level 2: 128 feature sample points for coarse candidate screening.
  - Level 3: Dynamic candidate list with worst-candidate replacement policy (guarantees the best matches are never discarded).
  - Level 4: Fine-resolution subpixel alignment on high-contrast feature pixels.
- **Blazing Fast**: Searches an entire 2560x1440 screen in **~150ms** with 99.9% match confidence.

### 2. 🖱️ Click Offset X & Y Controls & Cursor Settle Delay
- **Micro-Adjustment Offset**: Added **Click Offset X (px)** and **Click Offset Y (px)** input fields directly in the *Presets & Match Settings* panel. Allows fine-tuning click coordinates up, down, left, or right if a snipped image has uneven padding or requires targeting a specific part of an element.
- **Browser Event Reliability**: Added an internal 30ms cursor settle yield between cursor positioning and Win32 mouse click dispatch, ensuring Chromium, Firefox, and game engines update their hover target before the click event fires.

### 3. 🔍 Native Windows OCR in Ordered Steps Mode
- **Ordered Steps OCR Support**: In previous versions, Ordered Steps mode passed `null` to the OCR service, causing text targets (e.g. `Slow download`, `Claim`, `Next`) to report *"❌ No active target was found on screen"*.
- **Asynchronous Execution & Deadlock Prevention**: OCR calls now utilize non-blocking tasks with `.ConfigureAwait(false)` to prevent COM apartment and UI synchronization context stalls.

### 4. 📐 Restrict Search Area Box Alignment Fix
- **DPI-Aware Synchronization**: Fixed a coordinate space desync between Win32's `SetWindowPos` and WPF's layout engine in `SearchAreaWindow.cs`. The translucent blue visual bounding box now stays exactly where dragged without drifting away.

### 5. 🛡️ Startup Crash & Initialization Guard
- **Fixed `NullReferenceException`**: Moved `AppSettings.Load()` prior to `InitializeComponent()` and added initialization guards in all combo boxes and settings synchronization handlers, completely eliminating the startup error dialog.

### 6. 💾 Direct Preset Naming Box (`TbPresetName`)
- **Custom Preset Names**: Added a dedicated preset text box directly above the "💾 Save Preset" button. Type any custom preset name (e.g., `Nexus Fast Download`, `Daily Quests`) and press `Enter` to save instantly.

### 7. 📁 Universal Cross-Version Settings Persistence (`%APPDATA%\ApexClicker`)
- **Central Storage in `%APPDATA%\ApexClicker`**: Settings (`settings.json`), profiles (`profiles\visual_bot`), and templates (`templates`) are stored in the user profile directory. All configuration automatically carries forward across future versions without manual migration.

---

## 📦 Downloads & Verification

| Asset | Size | Description |
| :--- | :--- | :--- |
| **`ApexClicker.exe`** | ~66.9 MB | Native .NET 9 single-file executable (Zero installation required) |
| **`ApexClicker-v1.5.3-Instant.zip`** | ~61.0 MB | Portable compressed distribution archive |

---

## 🛠️ Deployed Locations
- `dist\ApexClicker.exe`
- `dist\ApexClicker-v1.5.3-Instant.zip`
- `C:\moddingtools\ApexClicker.exe`
- `C:\moddingtools\ApexClicker_v1.5_Native.exe`
- `C:\moddingtools\ApexClicker_v2_Native.exe`
- `C:\moddingtools\ApexClicker\ApexClicker.exe`
