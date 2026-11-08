using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public enum MouseButtonType
    {
        Left,
        Right,
        Middle
    }

    public enum ClickType
    {
        Single,
        Double
    }

    public class ClickEngine
    {
        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();

        public MouseButtonType Button { get; set; } = MouseButtonType.Left;
        public ClickType ClickType { get; set; } = ClickType.Single;
        public double TargetIntervalMs { get; set; } = 10.0; // 10ms = 100 CPS default
        public bool UseFixedCoord { get; set; } = false;
        public int FixedX { get; set; } = 0;
        public int FixedY { get; set; } = 0;
        public int RepeatCount { get; set; } = 0; // 0 = infinite
        public bool AntiDetection { get; set; } = false;
        public int JitterRadius { get; set; } = 2; // ±2px
        public double JitterTimingMs { get; set; } = 1.5; // ±1.5ms

        public long TotalClicks => Interlocked.Read(ref _totalClicks);
        private long _totalClicks;
        private double _currentCps;

        public bool IsRunning => _isRunning;

        public event Action<long, double>? StatsUpdated;
        public event Action<bool>? StateChanged;

        private readonly Random _rand = new();

        public void Start()
        {
            lock (_lock)
            {
                if (_isRunning) return;

                _isRunning = true;
                Interlocked.Exchange(ref _totalClicks, 0);
                _currentCps = 0;

                Win32Api.TimeBeginPeriod(1);

                _workerThread = new Thread(WorkerLoop)
                {
                    IsBackground = true,
                    Priority = ThreadPriority.Highest,
                    Name = "ApexClickEngineThread"
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
            uint downFlag, upFlag;
            switch (Button)
            {
                case MouseButtonType.Right:
                    downFlag = Win32Api.MOUSEEVENTF_RIGHTDOWN;
                    upFlag = Win32Api.MOUSEEVENTF_RIGHTUP;
                    break;
                case MouseButtonType.Middle:
                    downFlag = Win32Api.MOUSEEVENTF_MIDDLEDOWN;
                    upFlag = Win32Api.MOUSEEVENTF_MIDDLEUP;
                    break;
                default:
                    downFlag = Win32Api.MOUSEEVENTF_LEFTDOWN;
                    upFlag = Win32Api.MOUSEEVENTF_LEFTUP;
                    break;
            }

            long frequency = Stopwatch.Frequency;
            long clicksThisBatch = 0;
            long lastStatsTime = Stopwatch.GetTimestamp();

            long totalCount = 0;

            while (_isRunning)
            {
                long startCycle = Stopwatch.GetTimestamp();

                // Move if fixed coordinate
                if (UseFixedCoord)
                {
                    int targetX = FixedX;
                    int targetY = FixedY;
                    if (AntiDetection && JitterRadius > 0)
                    {
                        targetX += _rand.Next(-JitterRadius, JitterRadius + 1);
                        targetY += _rand.Next(-JitterRadius, JitterRadius + 1);
                    }
                    Win32Api.SetCursorPos(targetX, targetY);
                }

                // Send Click via mouse_event (universal, zero UIPI permission blocking)
                Win32Api.mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                if (TargetIntervalMs > 2.0)
                {
                    PreciseSleep(0.001, frequency); // 1ms down hold for game engines
                }
                Win32Api.mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);

                totalCount++;
                clicksThisBatch++;
                Interlocked.Increment(ref _totalClicks);

                if (ClickType == ClickType.Double)
                {
                    PreciseSleep(0.015, frequency); // 15ms double click gap
                    Win32Api.mouse_event(downFlag, 0, 0, 0, UIntPtr.Zero);
                    if (TargetIntervalMs > 2.0)
                    {
                        PreciseSleep(0.001, frequency);
                    }
                    Win32Api.mouse_event(upFlag, 0, 0, 0, UIntPtr.Zero);

                    totalCount++;
                    clicksThisBatch++;
                    Interlocked.Increment(ref _totalClicks);
                }

                // Check repeat limit
                if (RepeatCount > 0 && totalCount >= RepeatCount)
                {
                    _isRunning = false;
                    break;
                }

                // Calculate stats every 150ms
                long now = Stopwatch.GetTimestamp();
                double elapsedSec = (double)(now - lastStatsTime) / frequency;
                if (elapsedSec >= 0.15)
                {
                    _currentCps = clicksThisBatch / elapsedSec;
                    clicksThisBatch = 0;
                    lastStatsTime = now;
                    StatsUpdated?.Invoke(TotalClicks, _currentCps);
                }

                // Interval delay with microsecond spin-wait precision
                double interval = TargetIntervalMs;
                if (TargetIntervalMs > 2.0)
                {
                    interval = Math.Max(0.5, interval - 1.0);
                }
                if (AntiDetection && JitterTimingMs > 0)
                {
                    double jitter = (_rand.NextDouble() * 2.0 - 1.0) * JitterTimingMs;
                    interval = Math.Max(0.5, interval + jitter);
                }

                PreciseSleep(interval / 1000.0, frequency);
            }

            Win32Api.TimeEndPeriod(1);
            _isRunning = false;
            StateChanged?.Invoke(false);
            StatsUpdated?.Invoke(TotalClicks, 0);
        }

        private static void PreciseSleep(double seconds, long frequency)
        {
            if (seconds <= 0) return;

            long start = Stopwatch.GetTimestamp();
            long targetTicks = (long)(seconds * frequency);

            // Coarse sleep if delay > 2.5ms to save CPU
            if (seconds > 0.0025)
            {
                int sleepMs = (int)((seconds - 0.002) * 1000.0);
                if (sleepMs > 0)
                {
                    Thread.Sleep(sleepMs);
                }
            }

            // High-resolution spin for the final sub-millisecond precision
            while ((Stopwatch.GetTimestamp() - start) < targetTicks)
            {
                Thread.SpinWait(10);
            }
        }
    }
}
