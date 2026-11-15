# ApexClicker Pro v1.5.4 — Windows Shutdown & Reboot Crash Fix, Eager Tracing Resolution

We are pleased to release **ApexClicker Pro v1.5.4**, resolving an unhandled `FileNotFoundException` in WPF's internal `ControlsTraceLogger` during OS shutdown, reboot, and logoff events.

---

## 🌟 What's Fixed in v1.5.4

### 1. 🛡️ Resolved Windows Shutdown & Reboot Crash Dialog
- **Root Cause**: During OS shutdown, restart (e.g. following Windows Update installations), or user logoff, Windows broadcasts `WM_QUERYENDSESSION` (`0x0011`). WPF invokes `Application.CriticalShutdown`, which attempts to flush control usage statistics via `MS.Internal.Telemetry.PresentationFramework.ControlsTraceLogger.LogUsedControlsDetails()`. In single-file self-contained deployments, dynamically resolving `System.Diagnostics.Tracing.dll` during OS session teardown resulted in a `System.IO.FileNotFoundException`. The global dispatcher previously displayed a modal `ApexClicker Error` message box, halting Windows shutdown until dismissed.
- **Eager Assembly Resolution**: `AppDomain.CurrentDomain.AssemblyResolve` now immediately provides `typeof(System.Diagnostics.Tracing.EventSource).Assembly` from memory whenever `System.Diagnostics.Tracing` is queried, preventing missing file exceptions.
- **Native OS Session Hook (`0x0011` / `0x0016`)**: Added native message handling in `MainWindow.xaml.cs` to gracefully stop active click engines and commit application settings before approving Windows shutdown without delay.
- **Modal Suppression During Shutdown**: `DispatcherUnhandledException` now suppresses modal dialogs during session teardown, ensuring Windows restarts and shutdowns proceed unhindered while logging details to `%APPDATA%\ApexClicker\crash.log`.

---

## 📦 Downloads & Verification

| Asset | Size | Description |
| :--- | :--- | :--- |
| **`ApexClicker.exe`** | ~66.9 MB | Native .NET 9 single-file executable (Zero installation required) |
| **`ApexClicker-v1.5.4-Instant.zip`** | ~61.0 MB | Portable compressed distribution archive |

---

## 🛠️ Deployed Locations
- `dist\ApexClicker.exe`
- `dist\ApexClicker-v1.5.4-Instant.zip`
- `C:\moddingtools\ApexClicker.exe`
- `C:\moddingtools\ApexClicker_v1.5_Native.exe`
- `C:\moddingtools\ApexClicker_v2_Native.exe`
- `C:\moddingtools\ApexClicker\ApexClicker.exe`
