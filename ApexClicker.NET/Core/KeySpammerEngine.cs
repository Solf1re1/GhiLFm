using System;
using System.Collections.Generic;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class KeySpammerEngine
    {
        public string KeysString { get; set; } = "1, 2, 3, E";
        public int IntervalMs { get; set; } = 100;
        public int KeyHoldDurationMs { get; set; } = 15;

        private Thread? _workerThread;
        private volatile bool _isRunning;
        private readonly object _lock = new();

        public bool IsRunning => _isRunning;
        public event Action<bool>? StateChanged;

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
                    Name = "ApexKeySpammerThread"
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
            var vkList = ParseKeys(KeysString);
            if (vkList.Count == 0)
            {
                _isRunning = false;
                StateChanged?.Invoke(false);
                return;
            }

            while (_isRunning)
            {
                foreach (byte vk in vkList)
                {
                    if (!_isRunning) break;

                    // Press
                    Win32Api.keybd_event(vk, 0, 0, UIntPtr.Zero);
                    Thread.Sleep(Math.Max(5, KeyHoldDurationMs));
                    // Release
                    Win32Api.keybd_event(vk, 0, Win32Api.KEYEVENTF_KEYUP, UIntPtr.Zero);

                    Thread.Sleep(Math.Max(5, IntervalMs));
                }
            }

            Win32Api.TimeEndPeriod(1);
            _isRunning = false;
            StateChanged?.Invoke(false);
        }

        private static List<byte> ParseKeys(string raw)
        {
            var result = new List<byte>();
            var tokens = raw.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries);

            foreach (var tok in tokens)
            {
                string clean = tok.Trim().ToUpperInvariant();
                if (clean.Length == 1 && clean[0] >= 'A' && clean[0] <= 'Z')
                {
                    result.Add((byte)clean[0]);
                }
                else if (clean.Length == 1 && clean[0] >= '0' && clean[0] <= '9')
                {
                    result.Add((byte)clean[0]);
                }
                else if (clean == "SPACE") result.Add(0x20);
                else if (clean == "ENTER" || clean == "RETURN") result.Add(0x0D);
                else if (clean == "TAB") result.Add(0x09);
                else if (clean == "ESC" || clean == "ESCAPE") result.Add(0x1B);
                else if (clean.StartsWith("F") && int.TryParse(clean[1..], out int fNum) && fNum >= 1 && fNum <= 12)
                {
                    result.Add((byte)(0x6F + fNum)); // VK_F1 is 0x70
                }
            }
            return result;
        }
    }
}
