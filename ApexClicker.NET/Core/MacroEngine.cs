using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class MacroEvent
    {
        public string Kind { get; set; } = "click"; // "move", "click_down", "click_up", "key_down", "key_up", "scroll"
        public int X { get; set; }
        public int Y { get; set; }
        public uint Button { get; set; }
        public uint VkCode { get; set; }
        public double DelayMs { get; set; }
    }

    public class MacroEngine
    {
        public List<MacroEvent> Events { get; set; } = new();
        public double PlaybackSpeed { get; set; } = 1.0;
        public int LoopCount { get; set; } = 1;
        public bool RecordMouseMoves { get; set; } = false;

        private IntPtr _hMouseHook = IntPtr.Zero;
        private IntPtr _hKbdHook = IntPtr.Zero;
        private Win32Api.LowLevelProc? _mouseProc;
        private Win32Api.LowLevelProc? _kbdProc;

        private volatile bool _isRecording;
        private volatile bool _isPlaying;
        private long _lastEventTimestamp;
        private Thread? _playbackThread;

        public bool IsRecording => _isRecording;
        public bool IsPlaying => _isPlaying;

        public event Action<bool, bool>? StateChanged;
        public event Action<int>? EventCountUpdated;

        public void StartRecording()
        {
            if (_isRecording || _isPlaying) return;

            Events.Clear();
            _isRecording = true;
            _lastEventTimestamp = Stopwatch.GetTimestamp();

            _mouseProc = MouseHookCallback;
            _kbdProc = KbdHookCallback;

            IntPtr hMod = Win32Api.GetModuleHandle(null);
            _hMouseHook = Win32Api.SetWindowsHookEx(Win32Api.WH_MOUSE_LL, _mouseProc, hMod, 0);
            _hKbdHook = Win32Api.SetWindowsHookEx(Win32Api.WH_KEYBOARD_LL, _kbdProc, hMod, 0);

            StateChanged?.Invoke(_isRecording, _isPlaying);
        }

        public void StopRecording()
        {
            if (!_isRecording) return;

            _isRecording = false;

            if (_hMouseHook != IntPtr.Zero)
            {
                Win32Api.UnhookWindowsHookEx(_hMouseHook);
                _hMouseHook = IntPtr.Zero;
            }
            if (_hKbdHook != IntPtr.Zero)
            {
                Win32Api.UnhookWindowsHookEx(_hKbdHook);
                _hKbdHook = IntPtr.Zero;
            }

            SanitizeRecordedEvents();
            EventCountUpdated?.Invoke(Events.Count);
            StateChanged?.Invoke(_isRecording, _isPlaying);
        }

        public void ToggleRecording()
        {
            if (_isRecording) StopRecording();
            else StartRecording();
        }

        public void StartPlayback()
        {
            if (_isPlaying || _isRecording || Events.Count == 0) return;

            _isPlaying = true;
            Win32Api.TimeBeginPeriod(1);

            _playbackThread = new Thread(PlaybackLoop)
            {
                IsBackground = true,
                Priority = ThreadPriority.AboveNormal,
                Name = "ApexMacroPlaybackThread"
            };
            _playbackThread.Start();

            StateChanged?.Invoke(_isRecording, _isPlaying);
        }

        public void StopPlayback()
        {
            if (!_isPlaying) return;

            _isPlaying = false;
            Win32Api.TimeEndPeriod(1);
            StateChanged?.Invoke(_isRecording, _isPlaying);
        }

        public void TogglePlayback()
        {
            if (_isPlaying) StopPlayback();
            else StartPlayback();
        }

        private void PlaybackLoop()
        {
            int inputSize = Marshal.SizeOf(typeof(Win32Api.INPUT));
            long frequency = Stopwatch.Frequency;
            int currentLoop = 0;

            while (_isPlaying)
            {
                currentLoop++;
                for (int i = 0; i < Events.Count; i++)
                {
                    if (!_isPlaying) break;

                    var ev = Events[i];
                    double adjustedDelaySec = (ev.DelayMs / Math.Max(0.1, PlaybackSpeed)) / 1000.0;

                    // Sleep delay
                    if (adjustedDelaySec > 0.002)
                    {
                        int sleepMs = (int)((adjustedDelaySec - 0.001) * 1000.0);
                        if (sleepMs > 0) Thread.Sleep(sleepMs);
                    }
                    long start = Stopwatch.GetTimestamp();
                    long targetTicks = (long)(adjustedDelaySec * frequency);
                    while (Stopwatch.GetTimestamp() - start < targetTicks)
                    {
                        Thread.SpinWait(5);
                    }

                    // Replay action
                    if (ev.Kind == "move")
                    {
                        Win32Api.SetCursorPos(ev.X, ev.Y);
                    }
                    else if (ev.Kind == "click_down" || ev.Kind == "click_up")
                    {
                        Win32Api.SetCursorPos(ev.X, ev.Y);
                        uint dwFlag = ev.Kind == "click_down" ?
                            (ev.Button == 1 ? Win32Api.MOUSEEVENTF_RIGHTDOWN : Win32Api.MOUSEEVENTF_LEFTDOWN) :
                            (ev.Button == 1 ? Win32Api.MOUSEEVENTF_RIGHTUP : Win32Api.MOUSEEVENTF_LEFTUP);

                        var inp = new Win32Api.INPUT[]
                        {
                            new Win32Api.INPUT { type = Win32Api.INPUT_MOUSE, u = new Win32Api.INPUT_UNION { mi = new Win32Api.MOUSEINPUT { dwFlags = dwFlag } } }
                        };
                        Win32Api.SendInput(1, inp, inputSize);
                    }
                    else if (ev.Kind == "key_down" || ev.Kind == "key_up")
                    {
                        uint dwFlag = ev.Kind == "key_up" ? Win32Api.KEYEVENTF_KEYUP : 0;
                        Win32Api.keybd_event((byte)ev.VkCode, 0, dwFlag, UIntPtr.Zero);
                    }
                }

                if (LoopCount > 0 && currentLoop >= LoopCount)
                    break;
            }

            _isPlaying = false;
            Win32Api.TimeEndPeriod(1);
            StateChanged?.Invoke(_isRecording, _isPlaying);
        }

        private IntPtr MouseHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && _isRecording)
            {
                long now = Stopwatch.GetTimestamp();
                double dtMs = (double)(now - _lastEventTimestamp) / Stopwatch.Frequency * 1000.0;
                _lastEventTimestamp = now;

                int msg = wParam.ToInt32();
                var hookStruct = Marshal.PtrToStructure<Win32Api.MSLLHOOKSTRUCT>(lParam);

                if (msg == Win32Api.WM_LBUTTONDOWN)
                {
                    Events.Add(new MacroEvent { Kind = "click_down", X = hookStruct.pt.X, Y = hookStruct.pt.Y, Button = 0, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
                else if (msg == Win32Api.WM_LBUTTONUP)
                {
                    Events.Add(new MacroEvent { Kind = "click_up", X = hookStruct.pt.X, Y = hookStruct.pt.Y, Button = 0, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
                else if (msg == Win32Api.WM_RBUTTONDOWN)
                {
                    Events.Add(new MacroEvent { Kind = "click_down", X = hookStruct.pt.X, Y = hookStruct.pt.Y, Button = 1, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
                else if (msg == Win32Api.WM_RBUTTONUP)
                {
                    Events.Add(new MacroEvent { Kind = "click_up", X = hookStruct.pt.X, Y = hookStruct.pt.Y, Button = 1, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
                else if (msg == Win32Api.WM_MOUSEMOVE && RecordMouseMoves)
                {
                    if (dtMs >= 16.0) // 60 FPS throttle
                    {
                        Events.Add(new MacroEvent { Kind = "move", X = hookStruct.pt.X, Y = hookStruct.pt.Y, DelayMs = dtMs });
                        EventCountUpdated?.Invoke(Events.Count);
                    }
                }
            }
            return Win32Api.CallNextHookEx(_hMouseHook, nCode, wParam, lParam);
        }

        private IntPtr KbdHookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && _isRecording)
            {
                var kbd = Marshal.PtrToStructure<Win32Api.KBDLLHOOKSTRUCT>(lParam);
                int msg = wParam.ToInt32();

                // Filter F10 to prevent self-trigger loop
                if (kbd.vkCode == Win32Api.VK_F10)
                {
                    return Win32Api.CallNextHookEx(_hKbdHook, nCode, wParam, lParam);
                }

                long now = Stopwatch.GetTimestamp();
                double dtMs = (double)(now - _lastEventTimestamp) / Stopwatch.Frequency * 1000.0;
                _lastEventTimestamp = now;

                if (msg == Win32Api.WM_KEYDOWN || msg == Win32Api.WM_SYSKEYDOWN)
                {
                    Events.Add(new MacroEvent { Kind = "key_down", VkCode = kbd.vkCode, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
                else if (msg == Win32Api.WM_KEYUP || msg == Win32Api.WM_SYSKEYUP)
                {
                    Events.Add(new MacroEvent { Kind = "key_up", VkCode = kbd.vkCode, DelayMs = dtMs });
                    EventCountUpdated?.Invoke(Events.Count);
                }
            }
            return Win32Api.CallNextHookEx(_hKbdHook, nCode, wParam, lParam);
        }

        private void SanitizeRecordedEvents()
        {
            // Remove trailing Ctrl / Alt / Shift release artifacts from pressing Ctrl+F10 to stop
            while (Events.Count > 0)
            {
                var last = Events[^1];
                if ((last.Kind == "key_down" || last.Kind == "key_up") &&
                    (last.VkCode == Win32Api.VK_CONTROL || last.VkCode == Win32Api.VK_MENU || last.VkCode == Win32Api.VK_SHIFT || last.VkCode == 0xA2 || last.VkCode == 0xA3))
                {
                    Events.RemoveAt(Events.Count - 1);
                }
                else
                {
                    break;
                }
            }
        }

        public void SaveToFile(string path)
        {
            SanitizeRecordedEvents();
            string json = JsonSerializer.Serialize(Events, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(path, json);
        }

        public void LoadFromFile(string path)
        {
            if (!File.Exists(path)) return;
            string json = File.ReadAllText(path);
            var loaded = JsonSerializer.Deserialize<List<MacroEvent>>(json);
            if (loaded != null)
            {
                Events = loaded;
                SanitizeRecordedEvents();
                EventCountUpdated?.Invoke(Events.Count);
            }
        }
    }
}
