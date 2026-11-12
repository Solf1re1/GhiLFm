# ApexClicker Pro v1.5.2 — Visual Bot Match Text (Native Windows OCR) & Ordered Steps Sequence Overhaul

We are thrilled to release **ApexClicker Pro v1.5.2**, introducing direct on-screen **Text Matching** via Windows Native Optical Character Recognition (OCR) and an extensive overhaul of the **Ordered Steps** automation engine!

---

## 🌟 What's New in v1.5.2

### 1. 🔤 Match Text Option (Direct Screen OCR & Text Targets)
Visual Bot no longer requires manually snipping buttons to click on-screen text!
- **Windows Native OCR (`Windows.Media.Ocr`)**: Utilizes hardware-accelerated Windows 10/11 optical character recognition with 0 external dependencies or DLL bloat. Finds and clicks words on screen regardless of button styling, size, color, or background animations.
- **Word & Phrase Recognition**: Detects single words (`Claim`, `Play`, `Accept`, `OK`, `Start`, `Next`) or multi-word phrases (`Claim Reward`, `Play Now`, `Next Level`).
- **Quick Preset Pills**: One-click quick selection pills for common game and UI buttons (`Claim`, `Play`, `Accept`, `OK`, `Start`, `Next`, `Confirm`, `Close`, `Retry`).
- **Matching Rules**: Configure whole-word exact matching or substring matching (`Contains`), with optional case sensitivity.
- **Dual Engine Options**:
  - `👁️ Live Screen OCR`: Real-time text detection on screen.
  - `🖼️ Pre-rendered Font Template`: Generates a crisp transparent pixel template for ultra-fast 5ms template searching.

### 2. 🔢 Ordered Steps (1 ➔ 2 ➔ 3) Automation Engine Overhaul
- **Dynamic Live Step Status**: The UI status bar now actively indicates the sequence state:
  - `Step #1/3: Waiting for "Play" (Text OCR)...`
  - `Step #1/3: Clicked 'Play' (95.0%) at (800, 450)`
  - `Step #2/3: Waiting for 'Treasure Chest' (Image)...`
  - `🔁 Finished sequence (3 steps). Looping to Step #1...`
- **Eliminated Instant Step-Skipping Bug**: Previously, `SkipToNext` skipped steps every 100ms when a game screen took a moment to load. The engine now respects a configurable `Step Timeout` (default 5.0s), preventing premature skips.
- **Missing Step Configuration**: Choose between:
  - `⏳ Wait until visible` (Recommended for dialog animations and loading screens)
  - `⏭️ Skip after timeout` (Proceeds if an optional popup doesn't appear)
- **Step Badges & Type Icons in Targets List**: Each item card in the queue now prominently displays its sequence number (`[#1]`, `[#2]`, `[#3]`) and target type icon (`🔤` for text, `🖼️` for images).
- **One-Click Step Reordering (▲ / ▼)**: Quickly reorder steps up or down directly in the targets list without having to delete and re-add them.
- **Ordered Step Test Actions**: "🎯 Test & Click Target" and "🔍 Scan Only" now specifically validate and test the current active step in the sequence.

---

## 📦 Downloads & Verification

| Asset | Size | Description |
| :--- | :--- | :--- |
| **`ApexClicker.exe`** | ~28.7 MB | Native .NET 9 single-file executable (Zero installation required) |
| **`ApexClicker-v1.5.2-Instant.zip`** | ~7.2 MB | Portable compressed distribution archive |

---

## 🛠️ Verification & Quality Assurance
- **Build Status**: Built with Microsoft .NET 9.0 SDK (`net9.0-windows10.0.19041.0`) with **0 warnings and 0 errors**.
- **Display Compatibility**: Fully DPI-aware across 100%, 125%, 150%, and 200% Windows scaling displays.
- **Deployed Locations**:
  - `C:\moddingtools\ApexClicker.exe`
  - `C:\moddingtools\ApexClicker_v1.5_Native.exe`
  - `C:\moddingtools\ApexClicker_v2_Native.exe`
  - `C:\moddingtools\ApexClicker\ApexClicker.exe`
