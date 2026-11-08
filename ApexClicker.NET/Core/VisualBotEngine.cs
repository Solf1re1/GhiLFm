using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class VisualTargetItem
    {
        public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
        public string Name { get; set; } = "Target";
        public string FilePath { get; set; } = "";
        public bool IsEnabled { get; set; } = true;
        public int Width { get; set; }
        public int Height { get; set; }

        [JsonIgnore]
        public string DisplayDetails => $"{Width}x{Height} px • {(File.Exists(FilePath) ? "Ready" : "Missing File")}";
    }

    public enum VisualFlowMode
    {
        AnyMatch,
        OrderedSteps
    }

    public enum NotFoundBehavior
    {
        WaitThenProceed,
        SkipToNext
    }

    public enum CursorTravelSpeed
    {
        Fast = 150,
        Smooth = 250,
        Gentle = 400
    }

    public class VisualBotPreset
    {
        public string Name { get; set; } = "Default";
        public List<VisualTargetItem> Targets { get; set; } = new();
        public double ConfidenceThreshold { get; set; } = 0.60;
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;
        public ClickType ClickType { get; set; } = ClickType.Double;
        public bool SmoothMovement { get; set; } = true;
        public CursorTravelSpeed TravelSpeed { get; set; } = CursorTravelSpeed.Smooth;
        public double CooldownSec { get; set; } = 0.5;
        public int ScanIntervalMs { get; set; } = 100;
        public VisualFlowMode FlowMode { get; set; } = VisualFlowMode.AnyMatch;
        public NotFoundBehavior NotFoundMode { get; set; } = NotFoundBehavior.WaitThenProceed;
        public bool LoopQueue { get; set; } = true;
        public bool UseRegion { get; set; } = false;
        public int RegionX { get; set; } = 100;
        public int RegionY { get; set; } = 100;
        public int RegionWidth { get; set; } = 400;
        public int RegionHeight { get; set; } = 300;
    }

    public class VisualBotEngine
    {
        public ObservableCollection<VisualTargetItem> Targets { get; } = new();

        public double ConfidenceThreshold { get; set; } = 0.60; // 60% default (Similar mode)
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;
        public ClickType ClickType { get; set; } = ClickType.Double; // Double click default (open app / game item)
        public bool SmoothMovement { get; set; } = true;
        public CursorTravelSpeed TravelSpeed { get; set; } = CursorTravelSpeed.Smooth;
        public double CooldownSec { get; set; } = 0.5;
        public int ScanIntervalMs { get; set; } = 100;

        public VisualFlowMode FlowMode { get; set; } = VisualFlowMode.AnyMatch;
        public NotFoundBehavior NotFoundMode { get; set; } = NotFoundBehavior.WaitThenProceed;
        public bool LoopQueue { get; set; } = true;

        public bool UseRegion { get; set; } = false;
        public int RegionX { get; set; } = 100;
        public int RegionY { get; set; } = 100;
        public int RegionWidth { get; set; } = 400;
        public int RegionHeight { get; set; } = 300;
        public int ClickOffsetX { get; set; } = 0;
        public int ClickOffsetY { get; set; } = 0;

        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();
        private readonly Humanizer _humanizer = new();

        public bool IsRunning => _isRunning;

        public event Action<bool>? StateChanged;
        public event Action<string, Point, double>? MatchFound;
        public event Action<string>? StatusReported;

        public static string TemplatesDirectory
        {
            get
            {
                string dir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "templates");
                Directory.CreateDirectory(dir);
                return dir;
            }
        }

        public static string PresetsDirectory
        {
            get
            {
                string dir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "profiles", "visual_bot");
                Directory.CreateDirectory(dir);
                return dir;
            }
        }

        public void Start()
        {
            lock (_lock)
            {
                if (_isRunning) return;

                _isRunning = true;
                Win32Api.TimeBeginPeriod(1);

                _workerThread = new Thread(WorkerLoop)
                {
                    IsBackground = true,
                    Priority = ThreadPriority.AboveNormal,
                    Name = "ApexVisualBotThread"
                };
                _workerThread.Start();

                StateChanged?.Invoke(true);
            }
        }

        public void Stop()
        {
            lock (_lock)
            {
                if (!_isRunning) return;

                _isRunning = false;
                Win32Api.TimeEndPeriod(1);
                StateChanged?.Invoke(false);
            }
        }

        public void Toggle()
        {
            if (_isRunning) Stop();
            else Start();
        }

        private void WorkerLoop()
        {
            // Cache active bitmaps
            var activeTargets = new List<(VisualTargetItem item, Bitmap bmp)>();
            foreach (var target in Targets)
            {
                if (target.IsEnabled && File.Exists(target.FilePath))
                {
                    try
                    {
                        var bmp = new Bitmap(target.FilePath);
                        activeTargets.Add((target, bmp));
                    }
                    catch { }
                }
            }

            if (activeTargets.Count == 0)
            {
                StatusReported?.Invoke("No active targets found in queue.");
                _isRunning = false;
                Win32Api.TimeEndPeriod(1);
                StateChanged?.Invoke(false);
                return;
            }

            int currentOrderedIndex = 0;

            try
            {
                while (_isRunning)
                {
                    int screenW = Win32Api.GetSystemMetrics(0);
                    int screenH = Win32Api.GetSystemMetrics(1);

                    int searchX = UseRegion ? Math.Max(0, RegionX) : 0;
                    int searchY = UseRegion ? Math.Max(0, RegionY) : 0;
                    int searchW = UseRegion ? Math.Min(screenW - searchX, RegionWidth) : screenW;
                    int searchH = UseRegion ? Math.Min(screenH - searchY, RegionHeight) : screenH;

                    if (searchW <= 20 || searchH <= 20)
                    {
                        Thread.Sleep(ScanIntervalMs);
                        continue;
                    }

                    using (Bitmap screenBmp = new Bitmap(searchW, searchH, PixelFormat.Format32bppRgb))
                    {
                        using (Graphics g = Graphics.FromImage(screenBmp))
                        {
                            g.CopyFromScreen(searchX, searchY, 0, 0, new Size(searchW, searchH), CopyPixelOperation.SourceCopy);
                        }

                        if (FlowMode == VisualFlowMode.AnyMatch)
                        {
                            // Check all active targets
                            foreach (var (item, bmp) in activeTargets)
                            {
                                if (!_isRunning) break;
                                if (searchW < bmp.Width || searchH < bmp.Height) continue;

                                var match = FastTemplateSearch(screenBmp, bmp, ConfidenceThreshold);
                                if (match.HasValue)
                                {
                                    int clickX = searchX + match.Value.X + (bmp.Width / 2) + ClickOffsetX;
                                    int clickY = searchY + match.Value.Y + (bmp.Height / 2) + ClickOffsetY;

                                    ExecuteClick(clickX, clickY);
                                    MatchFound?.Invoke(item.Name, new Point(clickX, clickY), match.Value.Confidence);
                                    StatusReported?.Invoke($"Clicked {item.Name} ({match.Value.Confidence * 100:F1}%) at ({clickX}, {clickY})");

                                    // Cooldown wait
                                    if (CooldownSec > 0)
                                    {
                                        Thread.Sleep((int)(CooldownSec * 1000.0));
                                    }
                                    break; // Re-capture after action
                                }
                            }
                        }
                        else
                        {
                            // Ordered Steps Mode (1 -> 2 -> 3)
                            if (currentOrderedIndex >= activeTargets.Count)
                            {
                                if (LoopQueue) currentOrderedIndex = 0;
                                else
                                {
                                    _isRunning = false;
                                    break;
                                }
                            }

                            var (item, bmp) = activeTargets[currentOrderedIndex];
                            MatchResult? match = null;
                            if (searchW >= bmp.Width && searchH >= bmp.Height)
                            {
                                match = FastTemplateSearch(screenBmp, bmp, ConfidenceThreshold);
                            }

                            if (match.HasValue)
                            {
                                int clickX = searchX + match.Value.X + (bmp.Width / 2) + ClickOffsetX;
                                int clickY = searchY + match.Value.Y + (bmp.Height / 2) + ClickOffsetY;

                                ExecuteClick(clickX, clickY);
                                MatchFound?.Invoke(item.Name, new Point(clickX, clickY), match.Value.Confidence);
                                StatusReported?.Invoke($"Step #{currentOrderedIndex + 1}: Clicked {item.Name} ({match.Value.Confidence * 100:F1}%)");

                                currentOrderedIndex++;
                                if (CooldownSec > 0)
                                {
                                    Thread.Sleep((int)(CooldownSec * 1000.0));
                                }
                            }
                            else
                            {
                                if (NotFoundMode == NotFoundBehavior.SkipToNext)
                                {
                                    currentOrderedIndex++;
                                }
                            }
                        }
                    }

                    Thread.Sleep(Math.Max(15, ScanIntervalMs));
                }
            }
            finally
            {
                foreach (var (_, bmp) in activeTargets)
                {
                    bmp.Dispose();
                }

                Win32Api.TimeEndPeriod(1);
                _isRunning = false;
                StateChanged?.Invoke(false);
            }
        }

        private void ExecuteClick(int targetX, int targetY)
        {
            if (SmoothMovement)
            {
                Win32Api.GetCursorPos(out var current);
                _humanizer.MoveSmoothly(current.X, current.Y, targetX, targetY, (int)TravelSpeed);
            }
            else
            {
                Win32Api.SetCursorPos(targetX, targetY);
            }

            uint downFlag = Button switch
            {
                MouseButtonType.Right => Win32Api.MOUSEEVENTF_RIGHTDOWN,
                MouseButtonType.Middle => Win32Api.MOUSEEVENTF_MIDDLEDOWN,
                _ => Win32Api.MOUSEEVENTF_LEFTDOWN
            };
            uint upFlag = Button switch
            {
                MouseButtonType.Right => Win32Api.MOUSEEVENTF_RIGHTUP,
                MouseButtonType.Middle => Win32Api.MOUSEEVENTF_MIDDLEUP,
                _ => Win32Api.MOUSEEVENTF_LEFTUP
            };

            Win32Api.mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(2);
            Win32Api.mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);

            if (ClickType == ClickType.Double)
            {
                Thread.Sleep(15);
                Win32Api.mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                Thread.Sleep(2);
                Win32Api.mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
            }
        }

        // ================= TEST ACTIONS =================
        public (bool found, string targetName, Point pos, double confidence) TestScan()
        {
            int screenW = Win32Api.GetSystemMetrics(0);
            int screenH = Win32Api.GetSystemMetrics(1);

            int searchX = UseRegion ? Math.Max(0, RegionX) : 0;
            int searchY = UseRegion ? Math.Max(0, RegionY) : 0;
            int searchW = UseRegion ? Math.Min(screenW - searchX, RegionWidth) : screenW;
            int searchH = UseRegion ? Math.Min(screenH - searchY, RegionHeight) : screenH;

            using Bitmap screenBmp = new Bitmap(searchW, searchH, PixelFormat.Format32bppRgb);
            using (Graphics g = Graphics.FromImage(screenBmp))
            {
                g.CopyFromScreen(searchX, searchY, 0, 0, new Size(searchW, searchH), CopyPixelOperation.SourceCopy);
            }

            foreach (var target in Targets)
            {
                if (!target.IsEnabled || !File.Exists(target.FilePath)) continue;
                using var bmp = new Bitmap(target.FilePath);
                if (searchW < bmp.Width || searchH < bmp.Height) continue;

                var match = FastTemplateSearch(screenBmp, bmp, ConfidenceThreshold);
                if (match.HasValue)
                {
                    int clickX = searchX + match.Value.X + (bmp.Width / 2) + ClickOffsetX;
                    int clickY = searchY + match.Value.Y + (bmp.Height / 2) + ClickOffsetY;
                    return (true, target.Name, new Point(clickX, clickY), match.Value.Confidence);
                }
            }

            return (false, "", Point.Empty, 0);
        }

        public (bool found, string targetName, Point pos, double confidence) TestAndClick()
        {
            var res = TestScan();
            if (res.found)
            {
                ExecuteClick(res.pos.X, res.pos.Y);
            }
            return res;
        }

        // ================= PRESET MANAGEMENT =================
        public void SaveToPreset(string presetName)
        {
            var preset = new VisualBotPreset
            {
                Name = presetName,
                Targets = new List<VisualTargetItem>(Targets),
                ConfidenceThreshold = ConfidenceThreshold,
                Button = Button,
                ClickType = ClickType,
                SmoothMovement = SmoothMovement,
                TravelSpeed = TravelSpeed,
                CooldownSec = CooldownSec,
                ScanIntervalMs = ScanIntervalMs,
                FlowMode = FlowMode,
                NotFoundMode = NotFoundMode,
                LoopQueue = LoopQueue,
                UseRegion = UseRegion,
                RegionX = RegionX,
                RegionY = RegionY,
                RegionWidth = RegionWidth,
                RegionHeight = RegionHeight
            };

            string path = Path.Combine(PresetsDirectory, $"{presetName}.json");
            string json = JsonSerializer.Serialize(preset, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(path, json);
        }

        public bool LoadFromPreset(string presetName)
        {
            string path = Path.Combine(PresetsDirectory, $"{presetName}.json");
            if (!File.Exists(path)) return false;

            try
            {
                string json = File.ReadAllText(path);
                var preset = JsonSerializer.Deserialize<VisualBotPreset>(json);
                if (preset == null) return false;

                Targets.Clear();
                foreach (var t in preset.Targets)
                {
                    Targets.Add(t);
                }

                ConfidenceThreshold = preset.ConfidenceThreshold;
                Button = preset.Button;
                ClickType = preset.ClickType;
                SmoothMovement = preset.SmoothMovement;
                TravelSpeed = preset.TravelSpeed;
                CooldownSec = preset.CooldownSec;
                ScanIntervalMs = preset.ScanIntervalMs;
                FlowMode = preset.FlowMode;
                NotFoundMode = preset.NotFoundMode;
                LoopQueue = preset.LoopQueue;
                UseRegion = preset.UseRegion;
                RegionX = preset.RegionX;
                RegionY = preset.RegionY;
                RegionWidth = preset.RegionWidth;
                RegionHeight = preset.RegionHeight;

                return true;
            }
            catch
            {
                return false;
            }
        }

        public static List<string> GetAvailablePresets()
        {
            var list = new List<string>();
            try
            {
                var dir = PresetsDirectory;
                foreach (var file in Directory.GetFiles(dir, "*.json"))
                {
                    list.Add(Path.GetFileNameWithoutExtension(file));
                }
            }
            catch { }

            if (list.Count == 0)
            {
                list.Add("Default");
            }
            return list;
        }

        // ================= TEMPLATE SEARCH ALGORITHM =================
        private struct MatchResult
        {
            public int X;
            public int Y;
            public double Confidence;
        }

        private static unsafe MatchResult? FastTemplateSearch(Bitmap screen, Bitmap template, double minConfidence)
        {
            int sW = screen.Width, sH = screen.Height;
            int tW = template.Width, tH = template.Height;

            BitmapData sData = screen.LockBits(new Rectangle(0, 0, sW, sH), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            BitmapData tData = template.LockBits(new Rectangle(0, 0, tW, tH), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);

            try
            {
                byte* sPtr = (byte*)sData.Scan0;
                byte* tPtr = (byte*)tData.Scan0;

                int sStride = sData.Stride;
                int tStride = tData.Stride;

                int maxDiffPerPixel = 255 * 3;
                long totalPixels = tW * tH;
                long maxTotalDiff = totalPixels * maxDiffPerPixel;
                long thresholdDiff = (long)(maxTotalDiff * (1.0 - minConfidence));

                int stepX = Math.Max(1, tW / 12);
                int stepY = Math.Max(1, tH / 12);

                for (int y = 0; y <= sH - tH; y += 2)
                {
                    for (int x = 0; x <= sW - tW; x += 2)
                    {
                        long diffSum = 0;
                        bool rejected = false;

                        for (int ty = 0; ty < tH; ty += stepY)
                        {
                            byte* sRow = sPtr + (y + ty) * sStride + x * 4;
                            byte* tRow = tPtr + ty * tStride;

                            for (int tx = 0; tx < tW; tx += stepX)
                            {
                                int idx = tx * 4;
                                int bDiff = Math.Abs(sRow[idx] - tRow[idx]);
                                int gDiff = Math.Abs(sRow[idx + 1] - tRow[idx + 1]);
                                int rDiff = Math.Abs(sRow[idx + 2] - tRow[idx + 2]);

                                diffSum += (bDiff + gDiff + rDiff);
                                if (diffSum > (thresholdDiff / 4))
                                {
                                    rejected = true;
                                    break;
                                }
                            }
                            if (rejected) break;
                        }

                        if (!rejected)
                        {
                            long detailedDiff = 0;
                            for (int ty = 0; ty < tH; ty += 2)
                            {
                                byte* sRow = sPtr + (y + ty) * sStride + x * 4;
                                byte* tRow = tPtr + ty * tStride;
                                for (int tx = 0; tx < tW; tx += 2)
                                {
                                    int idx = tx * 4;
                                    detailedDiff += Math.Abs(sRow[idx] - tRow[idx]);
                                    detailedDiff += Math.Abs(sRow[idx + 1] - tRow[idx + 1]);
                                    detailedDiff += Math.Abs(sRow[idx + 2] - tRow[idx + 2]);
                                }
                            }

                            long verifiedMaxDiff = (totalPixels / 4) * maxDiffPerPixel;
                            double conf = 1.0 - ((double)detailedDiff / verifiedMaxDiff);
                            if (conf >= minConfidence)
                            {
                                return new MatchResult { X = x, Y = y, Confidence = conf };
                            }
                        }
                    }
                }
            }
            finally
            {
                screen.UnlockBits(sData);
                template.UnlockBits(tData);
            }

            return null;
        }
    }
}
