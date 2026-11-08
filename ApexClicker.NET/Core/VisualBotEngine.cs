using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class VisualBotEngine
    {
        public string TemplateImagePath { get; set; } = "";
        public bool UseRegion { get; set; } = false;
        public int RegionX { get; set; } = 0;
        public int RegionY { get; set; } = 0;
        public int RegionWidth { get; set; } = 400;
        public int RegionHeight { get; set; } = 300;
        public double ConfidenceThreshold { get; set; } = 0.85; // 85% match
        public int ScanIntervalMs { get; set; } = 150;
        public int ClickOffsetX { get; set; } = 0;
        public int ClickOffsetY { get; set; } = 0;
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;

        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();

        public bool IsRunning => _isRunning;

        public event Action<bool>? StateChanged;
        public event Action<Point, double>? MatchFound;

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
            if (string.IsNullOrWhiteSpace(TemplateImagePath) || !System.IO.File.Exists(TemplateImagePath))
            {
                _isRunning = false;
                StateChanged?.Invoke(false);
                return;
            }

            Bitmap templateBmp;
            try
            {
                templateBmp = new Bitmap(TemplateImagePath);
            }
            catch
            {
                _isRunning = false;
                StateChanged?.Invoke(false);
                return;
            }

            uint downFlag = Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTDOWN : Win32Api.MOUSEEVENTF_LEFTDOWN;
            uint upFlag = Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTUP : Win32Api.MOUSEEVENTF_LEFTUP;

            while (_isRunning)
            {
                int screenW = Win32Api.GetSystemMetrics(0);
                int screenH = Win32Api.GetSystemMetrics(1);

                int searchX = UseRegion ? Math.Max(0, RegionX) : 0;
                int searchY = UseRegion ? Math.Max(0, RegionY) : 0;
                int searchW = UseRegion ? Math.Min(screenW - searchX, RegionWidth) : screenW;
                int searchH = UseRegion ? Math.Min(screenH - searchY, RegionHeight) : screenH;

                if (searchW <= templateBmp.Width || searchH <= templateBmp.Height)
                {
                    Thread.Sleep(ScanIntervalMs);
                    continue;
                }

                using Bitmap screenBmp = new Bitmap(searchW, searchH, PixelFormat.Format32bppRgb);
                using (Graphics g = Graphics.FromImage(screenBmp))
                {
                    g.CopyFromScreen(searchX, searchY, 0, 0, new Size(searchW, searchH), CopyPixelOperation.SourceCopy);
                }

                var match = FastTemplateSearch(screenBmp, templateBmp, ConfidenceThreshold);
                if (match.HasValue)
                {
                    int foundScreenX = searchX + match.Value.X + (templateBmp.Width / 2) + ClickOffsetX;
                    int foundScreenY = searchY + match.Value.Y + (templateBmp.Height / 2) + ClickOffsetY;

                    MatchFound?.Invoke(new Point(foundScreenX, foundScreenY), match.Value.Confidence);

                    Win32Api.SetCursorPos(foundScreenX, foundScreenY);
                    Win32Api.mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                    Thread.Sleep(2);
                    Win32Api.mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);
                }

                Thread.Sleep(Math.Max(20, ScanIntervalMs));
            }

            templateBmp.Dispose();
            Win32Api.TimeEndPeriod(1);
            _isRunning = false;
            StateChanged?.Invoke(false);
        }

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

                // Step-sampled check for high-speed scanning
                int stepX = Math.Max(1, tW / 12);
                int stepY = Math.Max(1, tH / 12);

                for (int y = 0; y <= sH - tH; y += 2)
                {
                    for (int x = 0; x <= sW - tW; x += 2)
                    {
                        long diffSum = 0;
                        bool rejected = false;

                        // Fast sample test
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
                            // Detailed verification
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
