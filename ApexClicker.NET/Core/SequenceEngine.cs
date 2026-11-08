using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class SequencePoint
    {
        public int Id { get; set; }
        public int X { get; set; }
        public int Y { get; set; }
        public int DelayMs { get; set; } = 150;
        public MouseButtonType Button { get; set; } = MouseButtonType.Left;
        public ClickType ClickType { get; set; } = ClickType.Single;
    }

    public class SequenceEngine
    {
        public ObservableCollection<SequencePoint> Points { get; set; } = new();
        public int LoopCount { get; set; } = 0; // 0 = infinite
        public bool SmoothMovement { get; set; } = true;

        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();
        private readonly Humanizer _humanizer = new();

        public bool IsRunning => _isRunning;

        public event Action<bool>? StateChanged;
        public event Action<int>? ActivePointChanged;

        public void Start()
        {
            lock (_lock)
            {
                if (_isRunning || Points.Count == 0) return;

                _isRunning = true;
                Win32Api.TimeBeginPeriod(1);

                _workerThread = new Thread(WorkerLoop)
                {
                    IsBackground = true,
                    Priority = ThreadPriority.Highest,
                    Name = "ApexSequenceThread"
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
            int loops = 0;

            while (_isRunning)
            {
                loops++;
                for (int i = 0; i < Points.Count; i++)
                {
                    if (!_isRunning) break;

                    var pt = Points[i];
                    ActivePointChanged?.Invoke(i);

                    // Move to point
                    Win32Api.GetCursorPos(out var current);
                    (int targetX, int targetY) = _humanizer.ApplyOffsetJitter(pt.X, pt.Y);

                    if (SmoothMovement)
                    {
                        _humanizer.MoveSmoothly(current.X, current.Y, targetX, targetY, 80);
                    }
                    else
                    {
                        Win32Api.SetCursorPos(targetX, targetY);
                    }

                    // Click
                    uint downFlag = pt.Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTDOWN :
                                   (pt.Button == MouseButtonType.Middle ? Win32Api.MOUSEEVENTF_MIDDLEDOWN : Win32Api.MOUSEEVENTF_LEFTDOWN);
                    uint upFlag = pt.Button == MouseButtonType.Right ? Win32Api.MOUSEEVENTF_RIGHTUP :
                                 (pt.Button == MouseButtonType.Middle ? Win32Api.MOUSEEVENTF_MIDDLEUP : Win32Api.MOUSEEVENTF_LEFTUP);

                    var inputs = new Win32Api.INPUT[]
                    {
                        new Win32Api.INPUT { type = Win32Api.INPUT_MOUSE, u = new Win32Api.INPUT_UNION { mi = new Win32Api.MOUSEINPUT { dwFlags = downFlag } } },
                        new Win32Api.INPUT { type = Win32Api.INPUT_MOUSE, u = new Win32Api.INPUT_UNION { mi = new Win32Api.MOUSEINPUT { dwFlags = upFlag } } }
                    };

                    Win32Api.SendInput(2, inputs, inputSize);

                    if (pt.ClickType == ClickType.Double)
                    {
                        Thread.Sleep(15);
                        Win32Api.SendInput(2, inputs, inputSize);
                    }

                    // Delay
                    double delay = _humanizer.GetRandomJitteredInterval(pt.DelayMs);
                    Thread.Sleep(Math.Max(1, (int)delay));
                }

                if (LoopCount > 0 && loops >= LoopCount)
                {
                    break;
                }
            }

            _isRunning = false;
            Win32Api.TimeEndPeriod(1);
            StateChanged?.Invoke(false);
        }
    }
}
