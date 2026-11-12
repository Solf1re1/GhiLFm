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

    public enum VisualSelectionStrategy
    {
        HighestConfidence = 0,
        ClosestToCursor = 1
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

    public struct TemplatePixel
    {
        public short X;
        public short Y;
        public byte Gray;
    }

    public class PreparedTemplate : IDisposable
    {
        public VisualTargetItem Item { get; }
        public int Width { get; }
        public int Height { get; }
        public TemplatePixel[] Pixels { get; }
        public TemplatePixel[] AnchorPixels { get; }
        public int ValidCount { get; }
        public long MaxPossibleError { get; }

        public PreparedTemplate(VisualTargetItem item, Bitmap bmp)
        {
            Item = item;
            Width = bmp.Width;
            Height = bmp.Height;

            int w = bmp.Width;
            int h = bmp.Height;
            var pixelList = new List<TemplatePixel>(w * h);

            BitmapData data = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            try
            {
                unsafe
                {
                    byte* ptr = (byte*)data.Scan0;
                    int stride = data.Stride;

                    for (short y = 0; y < h; y++)
                    {
                        byte* row = ptr + y * stride;
                        for (short x = 0; x < w; x++)
                        {
                            int idx = x * 4;
                            byte b = row[idx];
                            byte g = row[idx + 1];
                            byte r = row[idx + 2];
                            byte a = row[idx + 3];

                            // Skip transparent background pixels (alpha < 32)
                            if (a >= 32)
                            {
                                byte gray = (byte)((r * 77 + g * 150 + b * 29) >> 8);
                                pixelList.Add(new TemplatePixel { X = x, Y = y, Gray = gray });
                            }
                        }
                    }
                }
            }
            finally
            {
                bmp.UnlockBits(data);
            }

            if (pixelList.Count == 0)
            {
                for (short y = 0; y < h; y++)
                {
                    for (short x = 0; x < w; x++)
                    {
                        pixelList.Add(new TemplatePixel { X = x, Y = y, Gray = 128 });
                    }
                }
            }

            Pixels = pixelList.ToArray();
            ValidCount = Pixels.Length;
            MaxPossibleError = ValidCount * 255L;

            // Sparse anchor pixels (48 pixels evenly distributed across the template for instantaneous coarse screening)
            if (pixelList.Count <= 48)
            {
                AnchorPixels = Pixels;
            }
            else
            {
                var anchors = new List<TemplatePixel>(48);
                int step = Math.Max(1, pixelList.Count / 48);
                for (int i = 0; i < pixelList.Count && anchors.Count < 48; i += step)
                {
                    anchors.Add(pixelList[i]);
                }
                AnchorPixels = anchors.ToArray();
            }
        }

        public void Dispose()
        {
        }
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
        public double ScanIntervalSec { get; set; } = 0.10;
        public VisualSelectionStrategy Strategy { get; set; } = VisualSelectionStrategy.HighestConfidence;

        [JsonPropertyName("ScanIntervalMs")]
        public int? LegacyScanIntervalMs
        {
            get => (int)(ScanIntervalSec * 1000.0);
            set { if (value.HasValue && value.Value > 0) ScanIntervalSec = value.Value / 1000.0; }
        }

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
        public double ScanIntervalSec { get; set; } = 0.10;
        public VisualSelectionStrategy Strategy { get; set; } = VisualSelectionStrategy.HighestConfidence;

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
                StatusReported?.Invoke("⚡ Visual Bot active • Scanning for targets...");

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
            // Cache prepared templates once
            var activeTemplates = new List<PreparedTemplate>();
            foreach (var target in Targets)
            {
                if (target.IsEnabled && File.Exists(target.FilePath))
                {
                    try
                    {
                        using var bmp = new Bitmap(target.FilePath);
                        activeTemplates.Add(new PreparedTemplate(target, bmp));
                    }
                    catch { }
                }
            }

            if (activeTemplates.Count == 0)
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
                        Thread.Sleep((int)(ScanIntervalSec * 1000.0));
                        continue;
                    }

                    using (Bitmap screenBmp = new Bitmap(searchW, searchH, PixelFormat.Format32bppRgb))
                    {
                        using (Graphics g = Graphics.FromImage(screenBmp))
                        {
                            g.CopyFromScreen(searchX, searchY, 0, 0, new Size(searchW, searchH), CopyPixelOperation.SourceCopy);
                        }

                        Win32Api.GetCursorPos(out var mousePt);
                        Point cursorPos = new Point(mousePt.X, mousePt.Y);

                        if (FlowMode == VisualFlowMode.AnyMatch)
                        {
                            PreparedTemplate? bestTarget = null;
                            MatchResult? bestMatch = null;
                            double bestDistSq = double.MaxValue;

                            foreach (var prep in activeTemplates)
                            {
                                if (!_isRunning) break;
                                if (searchW < prep.Width || searchH < prep.Height) continue;

                                var match = FastTemplateSearch(screenBmp, prep, ConfidenceThreshold, Strategy, searchX, searchY, cursorPos);
                                if (match.HasValue)
                                {
                                    if (Strategy == VisualSelectionStrategy.ClosestToCursor)
                                    {
                                        int cX = searchX + match.Value.X + (prep.Width / 2) + ClickOffsetX;
                                        int cY = searchY + match.Value.Y + (prep.Height / 2) + ClickOffsetY;
                                        double distSq = Math.Pow(cX - cursorPos.X, 2) + Math.Pow(cY - cursorPos.Y, 2);
                                        if (bestMatch == null || distSq < bestDistSq)
                                        {
                                            bestDistSq = distSq;
                                            bestMatch = match;
                                            bestTarget = prep;
                                        }
                                    }
                                    else
                                    {
                                        if (bestMatch == null || match.Value.Confidence > bestMatch.Value.Confidence)
                                        {
                                            bestMatch = match;
                                            bestTarget = prep;
                                        }
                                    }
                                }
                            }

                            if (bestMatch.HasValue && bestTarget != null)
                            {
                                int clickX = searchX + bestMatch.Value.X + (bestTarget.Width / 2) + ClickOffsetX;
                                int clickY = searchY + bestMatch.Value.Y + (bestTarget.Height / 2) + ClickOffsetY;

                                ExecuteClick(clickX, clickY);
                                MatchFound?.Invoke(bestTarget.Item.Name, new Point(clickX, clickY), bestMatch.Value.Confidence);
                                StatusReported?.Invoke($"Clicked {bestTarget.Item.Name} ({bestMatch.Value.Confidence * 100:F1}%) at ({clickX}, {clickY})");

                                if (CooldownSec > 0)
                                {
                                    Thread.Sleep((int)(CooldownSec * 1000.0));
                                }
                            }
                        }
                        else
                        {
                            // Ordered Steps Mode (1 -> 2 -> 3)
                            if (currentOrderedIndex >= activeTemplates.Count)
                            {
                                if (LoopQueue) currentOrderedIndex = 0;
                                else
                                {
                                    _isRunning = false;
                                    break;
                                }
                            }

                            var prep = activeTemplates[currentOrderedIndex];
                            MatchResult? match = null;
                            if (searchW >= prep.Width && searchH >= prep.Height)
                            {
                                match = FastTemplateSearch(screenBmp, prep, ConfidenceThreshold, Strategy, searchX, searchY, cursorPos);
                            }

                            if (match.HasValue)
                            {
                                int clickX = searchX + match.Value.X + (prep.Width / 2) + ClickOffsetX;
                                int clickY = searchY + match.Value.Y + (prep.Height / 2) + ClickOffsetY;

                                ExecuteClick(clickX, clickY);
                                MatchFound?.Invoke(prep.Item.Name, new Point(clickX, clickY), match.Value.Confidence);
                                StatusReported?.Invoke($"Step #{currentOrderedIndex + 1}: Clicked {prep.Item.Name} ({match.Value.Confidence * 100:F1}%)");

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

                    int sleepMs = Math.Max(10, (int)(ScanIntervalSec * 1000.0));
                    Thread.Sleep(sleepMs);
                }
            }
            finally
            {
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

            Win32Api.GetCursorPos(out var mousePt);
            Point cursorPos = new Point(mousePt.X, mousePt.Y);

            PreparedTemplate? bestPrep = null;
            MatchResult? bestMatch = null;
            double bestDistSq = double.MaxValue;

            foreach (var target in Targets)
            {
                if (!target.IsEnabled || !File.Exists(target.FilePath)) continue;
                using var bmp = new Bitmap(target.FilePath);
                if (searchW < bmp.Width || searchH < bmp.Height) continue;

                var prep = new PreparedTemplate(target, bmp);
                var match = FastTemplateSearch(screenBmp, prep, ConfidenceThreshold, Strategy, searchX, searchY, cursorPos);
                if (match.HasValue)
                {
                    if (Strategy == VisualSelectionStrategy.ClosestToCursor)
                    {
                        int cX = searchX + match.Value.X + (prep.Width / 2) + ClickOffsetX;
                        int cY = searchY + match.Value.Y + (prep.Height / 2) + ClickOffsetY;
                        double distSq = Math.Pow(cX - cursorPos.X, 2) + Math.Pow(cY - cursorPos.Y, 2);
                        if (bestMatch == null || distSq < bestDistSq)
                        {
                            bestDistSq = distSq;
                            bestMatch = match;
                            bestPrep = prep;
                        }
                    }
                    else
                    {
                        if (bestMatch == null || match.Value.Confidence > bestMatch.Value.Confidence)
                        {
                            bestMatch = match;
                            bestPrep = prep;
                        }
                    }
                }
            }

            if (bestMatch.HasValue && bestPrep != null)
            {
                int clickX = searchX + bestMatch.Value.X + (bestPrep.Width / 2) + ClickOffsetX;
                int clickY = searchY + bestMatch.Value.Y + (bestPrep.Height / 2) + ClickOffsetY;
                return (true, bestPrep.Item.Name, new Point(clickX, clickY), bestMatch.Value.Confidence);
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
                ScanIntervalSec = ScanIntervalSec,
                Strategy = Strategy,
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
                ScanIntervalSec = preset.ScanIntervalSec;
                Strategy = preset.Strategy;
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

        private static unsafe MatchResult? FastTemplateSearch(
            Bitmap screen, 
            PreparedTemplate template, 
            double minConfidence,
            VisualSelectionStrategy strategy = VisualSelectionStrategy.HighestConfidence,
            int searchOffsetX = 0,
            int searchOffsetY = 0,
            Point? targetCursorPos = null)
        {
            int sW = screen.Width, sH = screen.Height;
            int tW = template.Width, tH = template.Height;

            if (sW < tW || sH < tH) return null;

            int maxX = sW - tW;
            int maxY = sH - tH;

            // Convert screen to grayscale in flat cache-friendly buffer
            byte[] screenGray = new byte[sW * sH];
            BitmapData sData = screen.LockBits(new Rectangle(0, 0, sW, sH), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            try
            {
                byte* sPtr = (byte*)sData.Scan0;
                int sStride = sData.Stride;
                fixed (byte* gPtr = screenGray)
                {
                    for (int y = 0; y < sH; y++)
                    {
                        byte* sRow = sPtr + y * sStride;
                        byte* gRow = gPtr + y * sW;
                        for (int x = 0; x < sW; x++)
                        {
                            int idx = x * 4;
                            gRow[x] = (byte)((sRow[idx + 2] * 77 + sRow[idx + 1] * 150 + sRow[idx] * 29) >> 8);
                        }
                    }
                }
            }
            finally
            {
                screen.UnlockBits(sData);
            }

            var pixels = template.Pixels;
            var anchors = template.AnchorPixels ?? pixels;
            int numPixels = pixels.Length;
            int numAnchors = anchors.Length;
            if (numPixels == 0) return null;

            long maxAllowedError = (long)(numPixels * 255.0 * (1.0 - minConfidence));
            long maxAnchorError = (long)(numAnchors * 255.0 * (1.0 - minConfidence));

            if (strategy == VisualSelectionStrategy.ClosestToCursor && targetCursorPos.HasValue)
            {
                // Closest to Cursor:
                // Rapid anchor-screened candidate collection with thread-safe aggregation
                var candidates = new List<(int x, int y, long err)>();
                int minCandidateSpacing = Math.Max(12, Math.Min(tW, tH) / 2);
                object candLock = new object();
                int totalStepsY = (maxY / 2) + 1;

                Parallel.For(0, totalStepsY, (stepY) =>
                {
                    fixed (byte* gPtr = screenGray)
                    {
                        int sy = stepY * 2;
                        int rowOffset = sy * sW;

                        for (int sx = 0; sx <= maxX; sx += 2)
                        {
                            // 1. Instant 48-pixel anchor screening
                            long aErr = 0;
                            for (int i = 0; i < numAnchors; i++)
                            {
                                var ap = anchors[i];
                                int sVal = gPtr[rowOffset + ap.Y * sW + sx + ap.X];
                                int d = sVal - ap.Gray;
                                if (d < 0) d = -d;
                                aErr += d;
                                if (aErr > maxAnchorError) break;
                            }
                            if (aErr > maxAnchorError) continue;

                            // 2. Full pixel verification only for candidates passing anchor check
                            long err = 0;
                            for (int i = 0; i < numPixels; i++)
                            {
                                var p = pixels[i];
                                int screenVal = gPtr[rowOffset + p.Y * sW + sx + p.X];
                                int diff = screenVal - p.Gray;
                                if (diff < 0) diff = -diff;
                                err += diff;
                                if (err > maxAllowedError) break;
                            }

                            if (err <= maxAllowedError)
                            {
                                lock (candLock)
                                {
                                    bool merged = false;
                                    for (int c = 0; c < candidates.Count; c++)
                                    {
                                        if (Math.Abs(candidates[c].x - sx) < minCandidateSpacing &&
                                            Math.Abs(candidates[c].y - sy) < minCandidateSpacing)
                                        {
                                            if (err < candidates[c].err)
                                            {
                                                candidates[c] = (sx, sy, err);
                                            }
                                            merged = true;
                                            break;
                                        }
                                    }

                                    if (!merged && candidates.Count < 32)
                                    {
                                        candidates.Add((sx, sy, err));
                                    }
                                }
                            }
                        }
                    }
                });

                if (candidates.Count > 0)
                {
                    MatchResult? bestResult = null;
                    double minDistanceSq = double.MaxValue;

                    fixed (byte* gPtr = screenGray)
                    {
                        foreach (var cand in candidates)
                        {
                            int refMinX = Math.Max(0, cand.x - 2);
                            int refMaxX = Math.Min(maxX, cand.x + 2);
                            int refMinY = Math.Max(0, cand.y - 2);
                            int refMaxY = Math.Min(maxY, cand.y + 2);

                            long fineBestErr = cand.err;
                            int fineBestX = cand.x;
                            int fineBestY = cand.y;

                            for (int sy = refMinY; sy <= refMaxY; sy++)
                            {
                                int rowOffset = sy * sW;
                                for (int sx = refMinX; sx <= refMaxX; sx++)
                                {
                                    long err = 0;
                                    for (int i = 0; i < numPixels; i++)
                                    {
                                        var p = pixels[i];
                                        int screenVal = gPtr[rowOffset + p.Y * sW + sx + p.X];
                                        int diff = screenVal - p.Gray;
                                        if (diff < 0) diff = -diff;
                                        err += diff;
                                        if (err >= fineBestErr) break;
                                    }

                                    if (err < fineBestErr)
                                    {
                                        fineBestErr = err;
                                        fineBestX = sx;
                                        fineBestY = sy;
                                    }
                                }
                            }

                            double conf = 1.0 - ((double)fineBestErr / (numPixels * 255.0));
                            if (conf >= minConfidence)
                            {
                                int screenMatchX = searchOffsetX + fineBestX + (tW / 2);
                                int screenMatchY = searchOffsetY + fineBestY + (tH / 2);
                                double distSq = Math.Pow(screenMatchX - targetCursorPos.Value.X, 2) + 
                                                Math.Pow(screenMatchY - targetCursorPos.Value.Y, 2);

                                if (distSq < minDistanceSq)
                                {
                                    minDistanceSq = distSq;
                                    bestResult = new MatchResult { X = fineBestX, Y = fineBestY, Confidence = conf };
                                }
                            }
                        }
                    }

                    if (bestResult.HasValue) return bestResult;
                }
            }
            else
            {
                // Highest Confidence (Default):
                // Multi-core parallel scan with sparse anchor screening
                object searchLock = new object();
                long globalBestErr = maxAllowedError + 1;
                int globalBestX = -1;
                int globalBestY = -1;
                int totalStepsY = (maxY / 2) + 1;

                Parallel.For(0, totalStepsY, () => (bestErr: maxAllowedError + 1, bestX: -1, bestY: -1), (stepY, loopState, localState) =>
                {
                    fixed (byte* gPtr = screenGray)
                    {
                        int sy = stepY * 2;
                        int rowOffset = sy * sW;

                        for (int sx = 0; sx <= maxX; sx += 2)
                        {
                            // 1. Instant 48-pixel anchor screening (rejects 99.9% of non-matching points in ~10 ops)
                            long aErr = 0;
                            for (int i = 0; i < numAnchors; i++)
                            {
                                var ap = anchors[i];
                                int sVal = gPtr[rowOffset + ap.Y * sW + sx + ap.X];
                                int d = sVal - ap.Gray;
                                if (d < 0) d = -d;
                                aErr += d;
                                if (aErr > maxAnchorError) break;
                            }
                            if (aErr > maxAnchorError) continue;

                            // 2. Full pixel verification only for plausible target locations
                            long err = 0;
                            for (int i = 0; i < numPixels; i++)
                            {
                                var p = pixels[i];
                                int screenVal = gPtr[rowOffset + p.Y * sW + sx + p.X];
                                int diff = screenVal - p.Gray;
                                if (diff < 0) diff = -diff;
                                err += diff;
                                if (err >= localState.bestErr && err >= globalBestErr) break;
                            }

                            if (err < localState.bestErr)
                            {
                                localState = (err, sx, sy);
                            }
                        }
                    }

                    return localState;
                },
                (finalLocal) =>
                {
                    lock (searchLock)
                    {
                        if (finalLocal.bestX != -1 && finalLocal.bestErr < globalBestErr)
                        {
                            globalBestErr = finalLocal.bestErr;
                            globalBestX = finalLocal.bestX;
                            globalBestY = finalLocal.bestY;
                        }
                    }
                });

                // Pass 2: Local fine pixel search in ±2 neighborhood around the best candidate
                if (globalBestX != -1)
                {
                    int refMinX = Math.Max(0, globalBestX - 2);
                    int refMaxX = Math.Min(maxX, globalBestX + 2);
                    int refMinY = Math.Max(0, globalBestY - 2);
                    int refMaxY = Math.Min(maxY, globalBestY + 2);
                    long fineBestErr = globalBestErr;
                    int fineBestX = globalBestX;
                    int fineBestY = globalBestY;

                    fixed (byte* gPtr = screenGray)
                    {
                        for (int sy = refMinY; sy <= refMaxY; sy++)
                        {
                            int rowOffset = sy * sW;
                            for (int sx = refMinX; sx <= refMaxX; sx++)
                            {
                                long err = 0;
                                for (int i = 0; i < numPixels; i++)
                                {
                                    var p = pixels[i];
                                    int screenVal = gPtr[rowOffset + p.Y * sW + sx + p.X];
                                    int diff = screenVal - p.Gray;
                                    if (diff < 0) diff = -diff;
                                    err += diff;
                                    if (err >= fineBestErr) break;
                                }

                                if (err < fineBestErr)
                                {
                                    fineBestErr = err;
                                    fineBestX = sx;
                                    fineBestY = sy;
                                }
                            }
                        }
                    }

                    double confidence = 1.0 - ((double)fineBestErr / (numPixels * 255.0));
                    if (confidence >= minConfidence)
                    {
                        return new MatchResult { X = fineBestX, Y = fineBestY, Confidence = confidence };
                    }
                }
            }

            return null;
        }
    }
}
