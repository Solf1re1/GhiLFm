using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public enum VisualTargetType
    {
        Image = 0,
        TextOcr = 1,
        TextTemplate = 2
    }

    public class VisualTargetItem : INotifyPropertyChanged
    {
        public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
        public string Name { get; set; } = "Target";
        public string FilePath { get; set; } = "";
        public bool IsEnabled { get; set; } = true;
        public int Width { get; set; }
        public int Height { get; set; }

        public VisualTargetType TargetType { get; set; } = VisualTargetType.Image;
        public string TargetText { get; set; } = "";
        public bool ExactWordMatch { get; set; } = false;
        public bool CaseSensitive { get; set; } = false;

        public double StepDelaySec { get; set; } = 0.0;
        public double StepTimeoutSec { get; set; } = 5.0;

        private int _stepNumber = 1;
        [JsonIgnore]
        public int StepNumber
        {
            get => _stepNumber;
            set
            {
                if (_stepNumber != value)
                {
                    _stepNumber = value;
                    OnPropertyChanged(nameof(StepNumber));
                    OnPropertyChanged(nameof(StepBadge));
                }
            }
        }

        [JsonIgnore]
        public string StepBadge => $"#{StepNumber}";

        [JsonIgnore]
        public string TypeIcon => TargetType switch
        {
            VisualTargetType.TextOcr => "🔤",
            VisualTargetType.TextTemplate => "🔤",
            _ => "🖼️"
        };

        [JsonIgnore]
        public string DisplayDetails
        {
            get
            {
                if (TargetType == VisualTargetType.TextOcr)
                {
                    string matchDesc = ExactWordMatch ? "Exact Word" : "Contains";
                    return $"Text OCR: \"{TargetText}\" • {matchDesc}";
                }
                if (TargetType == VisualTargetType.TextTemplate)
                {
                    return $"Text Template: \"{TargetText}\" • {Width}x{Height} px";
                }
                return $"{Width}x{Height} px • {(File.Exists(FilePath) ? "Ready" : "Missing File")}";
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        public void OnPropertyChanged(string propName) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propName));
    }

    public enum VisualFlowMode
    {
        AnyMatch = 0,
        OrderedSteps = 1
    }

    public enum VisualSelectionStrategy
    {
        HighestConfidence = 0,
        ClosestToCursor = 1
    }

    public enum NotFoundBehavior
    {
        WaitThenProceed = 0,
        SkipToNext = 1
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

            // Sparse anchor pixels (48 pixels evenly distributed for fast coarse screening)
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

        public VisualFlowMode FlowMode { get; set; } = VisualFlowMode.AnyMatch;
        public NotFoundBehavior NotFoundMode { get; set; } = NotFoundBehavior.WaitThenProceed;
        public double StepTimeoutSec { get; set; } = 5.0;
        public bool LoopQueue { get; set; } = true;
        public bool UseRegion { get; set; } = false;
        public int RegionX { get; set; } = 100;
        public int RegionY { get; set; } = 100;
        public int RegionWidth { get; set; } = 400;
        public int RegionHeight { get; set; } = 300;
    }

    public class TargetMatchResult
    {
        public VisualTargetItem Target { get; set; } = null!;
        public Point CenterPos { get; set; }
        public double Confidence { get; set; }
    }

    public class VisualBotEngine
    {
        public ObservableCollection<VisualTargetItem> Targets { get; } = new();

        public double ConfidenceThreshold { get; set; } = 0.60;
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;
        public ClickType ClickType { get; set; } = ClickType.Double;
        public bool SmoothMovement { get; set; } = true;
        public CursorTravelSpeed TravelSpeed { get; set; } = CursorTravelSpeed.Smooth;
        public double CooldownSec { get; set; } = 0.5;
        public double ScanIntervalSec { get; set; } = 0.10;
        public VisualSelectionStrategy Strategy { get; set; } = VisualSelectionStrategy.HighestConfidence;

        public VisualFlowMode FlowMode { get; set; } = VisualFlowMode.AnyMatch;
        public NotFoundBehavior NotFoundMode { get; set; } = NotFoundBehavior.WaitThenProceed;
        public double StepTimeoutSec { get; set; } = 5.0;
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

        public static Bitmap GenerateTextTemplate(
            string text,
            string fontFamily = "Segoe UI",
            int fontSize = 16,
            bool bold = true,
            Color? textColor = null,
            Color? bgColor = null)
        {
            var style = bold ? FontStyle.Bold : FontStyle.Regular;
            using var tempBmp = new Bitmap(1, 1);
            using var tempG = Graphics.FromImage(tempBmp);
            using var font = new Font(fontFamily, fontSize, style, GraphicsUnit.Pixel);
            var size = tempG.MeasureString(text, font);
            int w = Math.Max(12, (int)Math.Ceiling(size.Width) + 8);
            int h = Math.Max(12, (int)Math.Ceiling(size.Height) + 6);

            var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
            using (var g = Graphics.FromImage(bmp))
            {
                g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;
                if (bgColor.HasValue)
                {
                    g.Clear(bgColor.Value);
                }
                else
                {
                    g.Clear(Color.Transparent);
                }

                using var brush = new SolidBrush(textColor ?? Color.White);
                g.DrawString(text, font, brush, 4, 3);
            }
            return bmp;
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
            var activeTargets = new List<VisualTargetItem>();
            var preparedMap = new Dictionary<string, PreparedTemplate>();

            foreach (var target in Targets)
            {
                if (target.IsEnabled)
                {
                    activeTargets.Add(target);
                    if (target.TargetType != VisualTargetType.TextOcr && File.Exists(target.FilePath))
                    {
                        try
                        {
                            using var bmp = new Bitmap(target.FilePath);
                            preparedMap[target.Id] = new PreparedTemplate(target, bmp);
                        }
                        catch { }
                    }
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

            int currentStepIndex = 0;
            DateTime stepStartTime = DateTime.UtcNow;
            string lastWaitingTargetId = "";

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
                            TargetMatchResult? bestResult = null;
                            double bestDistSq = double.MaxValue;

                            // Cache OCR result across targets if any OCR target is active
                            Windows.Media.Ocr.OcrResult? ocrResult = null;
                            bool ocrExecuted = false;

                            foreach (var target in activeTargets)
                            {
                                if (!_isRunning) break;

                                preparedMap.TryGetValue(target.Id, out var prep);
                                if (target.TargetType != VisualTargetType.TextOcr && prep == null) continue;

                                if (target.TargetType == VisualTargetType.TextOcr && !ocrExecuted)
                                {
                                    ocrResult = OcrService.RecognizeAsync(screenBmp).GetAwaiter().GetResult();
                                    ocrExecuted = true;
                                }

                                var match = FindTarget(screenBmp, target, prep, ocrResult, searchX, searchY, cursorPos);
                                if (match != null)
                                {
                                    if (Strategy == VisualSelectionStrategy.ClosestToCursor)
                                    {
                                        double distSq = Math.Pow(match.CenterPos.X - cursorPos.X, 2) + Math.Pow(match.CenterPos.Y - cursorPos.Y, 2);
                                        if (bestResult == null || distSq < bestDistSq)
                                        {
                                            bestDistSq = distSq;
                                            bestResult = match;
                                        }
                                    }
                                    else
                                    {
                                        if (bestResult == null || match.Confidence > bestResult.Confidence)
                                        {
                                            bestResult = match;
                                        }
                                    }
                                }
                            }

                            if (bestResult != null)
                            {
                                ExecuteClick(bestResult.CenterPos.X, bestResult.CenterPos.Y);
                                MatchFound?.Invoke(bestResult.Target.Name, bestResult.CenterPos, bestResult.Confidence);
                                StatusReported?.Invoke($"Clicked {bestResult.Target.Name} ({bestResult.Confidence * 100:F1}%) at ({bestResult.CenterPos.X}, {bestResult.CenterPos.Y})");

                                if (CooldownSec > 0)
                                {
                                    Thread.Sleep((int)(CooldownSec * 1000.0));
                                }
                            }
                        }
                        else
                        {
                            // ================= ORDERED STEPS MODE (1 -> 2 -> 3) =================
                            if (currentStepIndex >= activeTargets.Count)
                            {
                                if (LoopQueue)
                                {
                                    StatusReported?.Invoke($"🔁 Finished sequence ({activeTargets.Count} steps). Looping to Step #1...");
                                    currentStepIndex = 0;
                                    stepStartTime = DateTime.UtcNow;
                                    lastWaitingTargetId = "";
                                    if (CooldownSec > 0) Thread.Sleep((int)(CooldownSec * 1000.0));
                                    continue;
                                }
                                else
                                {
                                    StatusReported?.Invoke($"✅ Completed all {activeTargets.Count} ordered steps successfully!");
                                    _isRunning = false;
                                    break;
                                }
                            }

                            var currentTarget = activeTargets[currentStepIndex];

                            if (lastWaitingTargetId != currentTarget.Id)
                            {
                                string targetInfo = currentTarget.TargetType == VisualTargetType.TextOcr ? $"\"{currentTarget.TargetText}\" (Text OCR)" : $"'{currentTarget.Name}'";
                                StatusReported?.Invoke($"Step #{currentStepIndex + 1}/{activeTargets.Count}: Waiting for {targetInfo}...");
                                lastWaitingTargetId = currentTarget.Id;
                            }

                            preparedMap.TryGetValue(currentTarget.Id, out var prep);
                            var match = FindTarget(screenBmp, currentTarget, prep, null, searchX, searchY, cursorPos);

                            if (match != null)
                            {
                                ExecuteClick(match.CenterPos.X, match.CenterPos.Y);
                                MatchFound?.Invoke(currentTarget.Name, match.CenterPos, match.Confidence);
                                StatusReported?.Invoke($"Step #{currentStepIndex + 1}/{activeTargets.Count}: Clicked '{currentTarget.Name}' ({match.Confidence * 100:F1}%) at ({match.CenterPos.X}, {match.CenterPos.Y})");

                                double delay = currentTarget.StepDelaySec > 0 ? currentTarget.StepDelaySec : CooldownSec;
                                if (delay > 0)
                                {
                                    Thread.Sleep((int)(delay * 1000.0));
                                }

                                currentStepIndex++;
                                stepStartTime = DateTime.UtcNow;
                                lastWaitingTargetId = "";
                            }
                            else
                            {
                                if (NotFoundMode == NotFoundBehavior.SkipToNext)
                                {
                                    double timeout = currentTarget.StepTimeoutSec > 0 ? currentTarget.StepTimeoutSec : StepTimeoutSec;
                                    if (timeout > 0 && (DateTime.UtcNow - stepStartTime).TotalSeconds >= timeout)
                                    {
                                        StatusReported?.Invoke($"Step #{currentStepIndex + 1}/{activeTargets.Count}: '{currentTarget.Name}' timed out after {timeout:F1}s ➔ Skipping to next step.");
                                        currentStepIndex++;
                                        stepStartTime = DateTime.UtcNow;
                                        lastWaitingTargetId = "";
                                    }
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

        private TargetMatchResult? FindTarget(
            Bitmap screenBmp,
            VisualTargetItem target,
            PreparedTemplate? prep,
            Windows.Media.Ocr.OcrResult? cachedOcr,
            int searchX,
            int searchY,
            Point cursorPos)
        {
            if (target.TargetType == VisualTargetType.TextOcr)
            {
                List<TextMatchResult> matches;
                if (cachedOcr != null)
                {
                    matches = OcrService.ParseOcrResults(cachedOcr, target.TargetText, target.ExactWordMatch, target.CaseSensitive, searchX, searchY);
                }
                else
                {
                    matches = OcrService.FindText(screenBmp, target.TargetText, target.ExactWordMatch, target.CaseSensitive, searchX, searchY);
                }

                if (matches.Count > 0)
                {
                    TextMatchResult best = matches[0];
                    if (matches.Count > 1 && Strategy == VisualSelectionStrategy.ClosestToCursor)
                    {
                        double bestDist = double.MaxValue;
                        foreach (var m in matches)
                        {
                            double d = Math.Pow(m.CenterX + ClickOffsetX - cursorPos.X, 2) + Math.Pow(m.CenterY + ClickOffsetY - cursorPos.Y, 2);
                            if (d < bestDist)
                            {
                                bestDist = d;
                                best = m;
                            }
                        }
                    }

                    return new TargetMatchResult
                    {
                        Target = target,
                        CenterPos = new Point(best.CenterX + ClickOffsetX, best.CenterY + ClickOffsetY),
                        Confidence = best.Confidence
                    };
                }
                return null;
            }
            else
            {
                if (prep == null) return null;
                if (screenBmp.Width < prep.Width || screenBmp.Height < prep.Height) return null;

                var match = FastTemplateSearch(screenBmp, prep, ConfidenceThreshold, Strategy, searchX, searchY, cursorPos);
                if (match.HasValue)
                {
                    int clickX = searchX + match.Value.X + (prep.Width / 2) + ClickOffsetX;
                    int clickY = searchY + match.Value.Y + (prep.Height / 2) + ClickOffsetY;
                    return new TargetMatchResult
                    {
                        Target = target,
                        CenterPos = new Point(clickX, clickY),
                        Confidence = match.Value.Confidence
                    };
                }
                return null;
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

            // In OrderedSteps mode, test the first enabled target
            if (FlowMode == VisualFlowMode.OrderedSteps)
            {
                foreach (var target in Targets)
                {
                    if (!target.IsEnabled) continue;

                    PreparedTemplate? prep = null;
                    if (target.TargetType != VisualTargetType.TextOcr && File.Exists(target.FilePath))
                    {
                        using var bmp = new Bitmap(target.FilePath);
                        prep = new PreparedTemplate(target, bmp);
                    }

                    var match = FindTarget(screenBmp, target, prep, null, searchX, searchY, cursorPos);
                    if (match != null)
                    {
                        return (true, $"Step #1: {match.Target.Name}", match.CenterPos, match.Confidence);
                    }
                    else
                    {
                        return (false, $"Step #1: {target.Name}", Point.Empty, 0);
                    }
                }
            }
            else
            {
                // AnyMatch mode: find best candidate across all active targets
                TargetMatchResult? bestResult = null;
                double bestDistSq = double.MaxValue;
                Windows.Media.Ocr.OcrResult? ocrResult = null;
                bool ocrRun = false;

                foreach (var target in Targets)
                {
                    if (!target.IsEnabled) continue;

                    PreparedTemplate? prep = null;
                    if (target.TargetType != VisualTargetType.TextOcr && File.Exists(target.FilePath))
                    {
                        using var bmp = new Bitmap(target.FilePath);
                        prep = new PreparedTemplate(target, bmp);
                    }

                    if (target.TargetType == VisualTargetType.TextOcr && !ocrRun)
                    {
                        ocrResult = OcrService.RecognizeAsync(screenBmp).GetAwaiter().GetResult();
                        ocrRun = true;
                    }

                    var match = FindTarget(screenBmp, target, prep, ocrResult, searchX, searchY, cursorPos);
                    if (match != null)
                    {
                        if (Strategy == VisualSelectionStrategy.ClosestToCursor)
                        {
                            double distSq = Math.Pow(match.CenterPos.X - cursorPos.X, 2) + Math.Pow(match.CenterPos.Y - cursorPos.Y, 2);
                            if (bestResult == null || distSq < bestDistSq)
                            {
                                bestDistSq = distSq;
                                bestResult = match;
                            }
                        }
                        else
                        {
                            if (bestResult == null || match.Confidence > bestResult.Confidence)
                            {
                                bestResult = match;
                            }
                        }
                    }
                }

                if (bestResult != null)
                {
                    return (true, bestResult.Target.Name, bestResult.CenterPos, bestResult.Confidence);
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
                ScanIntervalSec = ScanIntervalSec,
                Strategy = Strategy,
                FlowMode = FlowMode,
                NotFoundMode = NotFoundMode,
                StepTimeoutSec = StepTimeoutSec,
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
                int idx = 1;
                foreach (var t in preset.Targets)
                {
                    t.StepNumber = idx++;
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
                StepTimeoutSec = preset.StepTimeoutSec;
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
