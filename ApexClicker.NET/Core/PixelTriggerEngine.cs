using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public enum PixelTriggerMode
    {
        ClickOnceOnMatch,
        SpamWhileMatching,
        TriggerOnColorChange
    }

    public class PixelTriggerEngine
    {
        public int TargetX { get; set; } = 500;
        public int TargetY { get; set; } = 500;
        public Color TargetColor { get; set; } = Color.FromArgb(0, 255, 0); // Default Green
        public int Tolerance { get; set; } = 15;
        public PixelTriggerMode Mode { get; set; } = PixelTriggerMode.ClickOnceOnMatch;
        public int ActionDelayMs { get; set; } = 100;
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;

        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();

        public bool IsRunning => _isRunning;

        public event Action<bool>? StateChanged;
        public event Action<Color>? ColorInspected;

        public static Color SamplePixelAtCursor(out int x, out int y)
        {
            Win32Api.GetCursorPos(out var pt);
            x = pt.X;
            y = pt.Y;
            return GetPixelColor(x, y);
        }

        public static Color GetPixelColor(int x, int y)
        {
            IntPtr hdc = Win32Api.GetDC(IntPtr.Zero);
            try
            {
                uint pixel = Win32Api.GetPixel(hdc, x, y);
                // Win32 GetPixel returns 0x00BBGGRR
                byte r = (byte)(pixel & 0x000000FF);
                byte g = (byte)((pixel & 0x0000FF00) >> 8);
                byte b = (byte)((pixel & 0x00FF0000) >> 16);
                return Color.FromArgb(r, g, b);
            }
            finally
            {
                Win32Api.ReleaseDC(IntPtr.Zero, hdc);
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
                    Name = "ApexPixelTriggerThread"
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
            int inputSize = Marshal.SizeOf(typeof(Win32Api.INPUT));
            uint downFlag = Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTDOWN : Win32Api.MOUSEEVENTF_LEFTDOWN;
            uint upFlag = Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTUP : Win32Api.MOUSEEVENTF_LEFTUP;

            var inputs = new Win32Api.INPUT[]
            {
                new Win32Api.INPUT { type = Win32Api.INPUT_MOUSE, u = new Win32Api.INPUT_UNION { mi = new Win32Api.MOUSEINPUT { dwFlags = downFlag } } },
                new Win32Api.INPUT { type = Win32Api.INPUT_MOUSE, u = new Win32Api.INPUT_UNION { mi = new Win32Api.MOUSEINPUT { dwFlags = upFlag } } }
            };

            bool wasMatching = false;

            while (_isRunning)
            {
                Color current = GetPixelColor(TargetX, TargetY);
                ColorInspected?.Invoke(current);

                bool isMatch = ColorMatches(current, TargetColor, Tolerance);

                if (Mode == PixelTriggerMode.ClickOnceOnMatch)
                {
                    if (isMatch && !wasMatching)
                    {
                        Win32Api.SendInput(2, inputs, inputSize);
                        wasMatching = true;
                    }
                    else if (!isMatch)
                    {
                        wasMatching = false;
                    }
                }
                else if (Mode == PixelTriggerMode.SpamWhileMatching)
                {
                    if (isMatch)
                    {
                        Win32Api.SendInput(2, inputs, inputSize);
                    }
                }
                else if (Mode == PixelTriggerMode.TriggerOnColorChange)
                {
                    if (!isMatch && wasMatching)
                    {
                        Win32Api.SendInput(2, inputs, inputSize);
                    }
                    wasMatching = isMatch;
                }

                Thread.Sleep(Math.Max(5, ActionDelayMs));
            }

            Win32Api.TimeEndPeriod(1);
            _isRunning = false;
            StateChanged?.Invoke(false);
        }

        private static bool ColorMatches(Color c1, Color c2, int tolerance)
        {
            int diffR = Math.Abs(c1.R - c2.R);
            int diffG = Math.Abs(c1.G - c2.G);
            int diffB = Math.Abs(c1.B - c2.B);
            return (diffR <= tolerance && diffG <= tolerance && diffB <= tolerance);
        }
    }
}
