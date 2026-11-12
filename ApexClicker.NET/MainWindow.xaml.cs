using System;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using ApexClicker.Core;
using ApexClicker.Native;

namespace ApexClicker
{
    public partial class MainWindow : Window
    {
        private readonly ClickEngine _clickEngine = new();
        private readonly SequenceEngine _sequenceEngine = new();
        private readonly PixelTriggerEngine _pixelEngine = new();
        private readonly VisualBotEngine _visualEngine = new();
        private readonly KeySpammerEngine _keySpamEngine = new();
        private readonly MacroEngine _macroEngine = new();
        private readonly AppSettings _settings;

        private HwndSource? _hwndSource;
        private const int HOTKEY_ID_TOGGLE = 9001;
        private const int HOTKEY_ID_PICK_POINT = 9002;
        private const int HOTKEY_ID_SAMPLE_PIXEL = 9003;
        private const int HOTKEY_ID_MACRO_TOGGLE = 9004;
        private const int HOTKEY_ID_COMPACT_TOGGLE = 9005;

        private OverlayWindow? _overlayWindow;
        private SearchAreaWindow? _searchAreaOverlay;
        private string _activeTabKey = "burst";
        private bool _isInitializing = true;

        public MainWindow()
        {
            _isInitializing = true;
            InitializeComponent();

            _settings = AppSettings.Load();

            // Hook Stats and States
            _clickEngine.StatsUpdated += OnEngineStatsUpdated;
            _clickEngine.StateChanged += (running) => OnEngineStateChanged(running, "CLICKER");

            _sequenceEngine.StateChanged += (running) => OnEngineStateChanged(running, "SEQUENCE");
            _pixelEngine.StateChanged += (running) => OnEngineStateChanged(running, "PIXEL");
            _visualEngine.StateChanged += (running) => OnEngineStateChanged(running, "VISUAL");
            _keySpamEngine.StateChanged += (running) => OnEngineStateChanged(running, "KEYSPAM");

            _visualEngine.StatusReported += (msg) =>
            {
                Dispatcher.InvokeAsync(() =>
                {
                    if (TxtVisualStatus != null) TxtVisualStatus.Text = msg;
                });
            };

            _macroEngine.StateChanged += (recording, playing) =>
            {
                Dispatcher.InvokeAsync(() =>
                {
                    BtnMacroRecord.Content = recording ? "⏹️ Stop Recording [Ctrl+F10]" : "⏺️ Start Recording [Ctrl+F10]";
                    BtnMacroPlay.Content = playing ? "⏹️ Stop Playback" : "▶️ Play Macro";
                    OnEngineStateChanged(playing, "MACRO");
                });
            };

            _macroEngine.EventCountUpdated += (count) =>
            {
                Dispatcher.InvokeAsync(() =>
                {
                    TxtMacroEventsCount.Text = $"Recorded Events: {count:N0}";
                });
            };

            Loaded += MainWindow_Loaded;
            Closed += MainWindow_Closed;

            SequenceItemsList.ItemsSource = _sequenceEngine.Points;
            VisualTargetsList.ItemsSource = _visualEngine.Targets;
            _visualEngine.Targets.CollectionChanged += (s, e) => UpdateVisualTargetCount();
        }

        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            var helper = new WindowInteropHelper(this);
            _hwndSource = HwndSource.FromHwnd(helper.Handle);
            _hwndSource?.AddHook(HwndHook);

            // Register Hotkeys
            Win32Api.RegisterHotKey(helper.Handle, HOTKEY_ID_TOGGLE, Win32Api.MOD_CONTROL, Win32Api.VK_F6);
            Win32Api.RegisterHotKey(helper.Handle, HOTKEY_ID_PICK_POINT, Win32Api.MOD_CONTROL, Win32Api.VK_F8);
            Win32Api.RegisterHotKey(helper.Handle, HOTKEY_ID_SAMPLE_PIXEL, Win32Api.MOD_CONTROL, Win32Api.VK_F9);
            Win32Api.RegisterHotKey(helper.Handle, HOTKEY_ID_MACRO_TOGGLE, Win32Api.MOD_CONTROL, Win32Api.VK_F10);
            Win32Api.RegisterHotKey(helper.Handle, HOTKEY_ID_COMPACT_TOGGLE, Win32Api.MOD_CONTROL, Win32Api.VK_M);

            // Apply Saved Theme
            ThemeManager.ApplyTheme(this, _settings.Theme);
            if (TxtActiveTheme != null)
            {
                TxtActiveTheme.Text = $"Active Theme: {_settings.Theme}";
            }

            // Apply Saved Module Toggles
            SyncModuleCheckboxes();
            ApplyModuleVisibility();
            RefreshNavButtons();

            // Load Visual Bot Presets & Settings
            LoadVisualPresetsCombo();
            LoadVisualSettingsFromAppConfig();
            UpdateVisualTargetCount();

            _isInitializing = false;
        }

        private void MainWindow_Closed(object? sender, EventArgs e)
        {
            StopAllEngines();
            _overlayWindow?.Close();
            _searchAreaOverlay?.Close();
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
            var helper = new WindowInteropHelper(this);
            Win32Api.UnregisterHotKey(helper.Handle, HOTKEY_ID_TOGGLE);
            Win32Api.UnregisterHotKey(helper.Handle, HOTKEY_ID_PICK_POINT);
            Win32Api.UnregisterHotKey(helper.Handle, HOTKEY_ID_SAMPLE_PIXEL);
            Win32Api.UnregisterHotKey(helper.Handle, HOTKEY_ID_MACRO_TOGGLE);
            Win32Api.UnregisterHotKey(helper.Handle, HOTKEY_ID_COMPACT_TOGGLE);
        }

        private IntPtr HwndHook(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == Win32Api.WM_HOTKEY)
            {
                int id = wParam.ToInt32();
                if (id == HOTKEY_ID_TOGGLE)
                {
                    HandleMasterToggle();
                    handled = true;
                }
                else if (id == HOTKEY_ID_PICK_POINT)
                {
                    BtnPickSeqCursor_Click(this, new RoutedEventArgs());
                    handled = true;
                }
                else if (id == HOTKEY_ID_SAMPLE_PIXEL)
                {
                    BtnSamplePixel_Click(this, new RoutedEventArgs());
                    handled = true;
                }
                else if (id == HOTKEY_ID_MACRO_TOGGLE)
                {
                    _macroEngine.ToggleRecording();
                    handled = true;
                }
                else if (id == HOTKEY_ID_COMPACT_TOGGLE)
                {
                    ToggleCompactMode();
                    handled = true;
                }
            }
            return IntPtr.Zero;
        }

        private void StopAllEngines()
        {
            _clickEngine.Stop();
            _sequenceEngine.Stop();
            _pixelEngine.Stop();
            _visualEngine.Stop();
            _keySpamEngine.Stop();
            _macroEngine.StopPlayback();
            _macroEngine.StopRecording();
        }

        private bool IsAnyEngineRunning()
        {
            return _clickEngine.IsRunning || _sequenceEngine.IsRunning || _pixelEngine.IsRunning ||
                   _visualEngine.IsRunning || _keySpamEngine.IsRunning || _macroEngine.IsPlaying;
        }

        public void HandleMasterToggle()
        {
            if (IsAnyEngineRunning())
            {
                StopAllEngines();
                return;
            }

            // Start currently active module
            switch (_activeTabKey)
            {
                case "sequence":
                    _sequenceEngine.Start();
                    break;
                case "pixel":
                    if (int.TryParse(TbPixelX.Text, out int px)) _pixelEngine.TargetX = px;
                    if (int.TryParse(TbPixelY.Text, out int py)) _pixelEngine.TargetY = py;
                    _pixelEngine.Start();
                    break;
                case "visual":
                    SyncVisualEngineSettings();
                    _visualEngine.Start();
                    break;
                case "keyspam":
                    _keySpamEngine.KeysString = TbKeySpamKeys.Text;
                    if (int.TryParse(TbKeySpamInterval.Text, out int ki)) _keySpamEngine.IntervalMs = ki;
                    _keySpamEngine.Start();
                    break;
                case "macro":
                    _macroEngine.StartPlayback();
                    break;
                default:
                    if (SliderCps != null && SliderCps.Value > 0)
                        _clickEngine.TargetIntervalMs = 1000.0 / Math.Max(1.0, SliderCps.Value);
                    if (CmbMouseButton != null)
                        _clickEngine.Button = CmbMouseButton.SelectedIndex switch
                        {
                            1 => MouseButtonType.Right,
                            2 => MouseButtonType.Middle,
                            _ => MouseButtonType.Left
                        };
                    if (CmbClickMode != null)
                        _clickEngine.ClickType = CmbClickMode.SelectedIndex switch
                        {
                            1 => ClickType.Double,
                            _ => ClickType.Single
                        };
                    if (RbFixed != null)
                        _clickEngine.UseFixedCoord = RbFixed.IsChecked == true;
                    if (int.TryParse(TbCoordX?.Text, out int fx)) _clickEngine.FixedX = fx;
                    if (int.TryParse(TbCoordY?.Text, out int fy)) _clickEngine.FixedY = fy;

                    _clickEngine.Start();
                    break;
            }
        }

        private void OnEngineStateChanged(bool isRunning, string engineName)
        {
            Dispatcher.InvokeAsync(() =>
            {
                if (isRunning)
                {
                    TxtStatus.Text = $"● ACTIVE ({engineName})";
                    TxtStatus.Foreground = (System.Windows.Media.Brush)Application.Current.Resources["ColorSuccess"];
                    BtnMasterToggle.Content = "⏹️ STOP [Ctrl+F6]";
                    BtnMasterToggle.Background = (System.Windows.Media.Brush)Application.Current.Resources["ColorDanger"];
                }
                else
                {
                    TxtStatus.Text = "● STOPPED [Ctrl+F6]";
                    TxtStatus.Foreground = (System.Windows.Media.Brush)Application.Current.Resources["ColorDanger"];
                    BtnMasterToggle.Content = "▶️ START [Ctrl+F6]";
                    BtnMasterToggle.Background = (System.Windows.Media.Brush)Application.Current.Resources["ColorSuccess"];
                }

                if (_overlayWindow != null && _overlayWindow.IsVisible)
                {
                    long clicks = long.TryParse(TxtClicks.Text.Replace(",", ""), out var c) ? c : 0;
                    double cps = double.TryParse(TxtCps.Text.Replace(" CPS", ""), out var s) ? s : 0;
                    _overlayWindow.UpdateStats(clicks, cps, isRunning, engineName);
                }
            });
        }

        private void OnEngineStatsUpdated(long totalClicks, double currentCps)
        {
            Dispatcher.InvokeAsync(() =>
            {
                TxtClicks.Text = totalClicks.ToString("N0");
                TxtCps.Text = $"{Math.Round(currentCps)} CPS";

                if (_overlayWindow != null && _overlayWindow.IsVisible)
                {
                    _overlayWindow.UpdateStats(totalClicks, currentCps, IsAnyEngineRunning(), GetActiveEngineName());
                }
            });
        }

        private void BtnMasterToggle_Click(object sender, RoutedEventArgs e)
        {
            HandleMasterToggle();
        }

        // ================= BURST CONTROLS =================
        private void SliderCps_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (TxtCpsSliderValue == null) return;
            double cps = Math.Round(e.NewValue);
            double interval = Math.Round(1000.0 / Math.Max(1.0, cps), 1);
            TxtCpsSliderValue.Text = $"{cps} CPS ({interval} ms)";
            _clickEngine.TargetIntervalMs = interval;
        }

        private void PresetCps_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string s && double.TryParse(s, out double cps))
            {
                SliderCps.Value = cps;
            }
        }

        private void CmbMouseButton_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            _clickEngine.Button = CmbMouseButton.SelectedIndex switch
            {
                1 => MouseButtonType.Right,
                2 => MouseButtonType.Middle,
                _ => MouseButtonType.Left
            };
        }

        private void CmbClickMode_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            _clickEngine.ClickType = CmbClickMode.SelectedIndex switch
            {
                1 => ClickType.Double,
                _ => ClickType.Single
            };
        }

        private void RbTarget_Changed(object sender, RoutedEventArgs e)
        {
            _clickEngine.UseFixedCoord = RbFixed?.IsChecked == true;
            if (int.TryParse(TbCoordX?.Text, out int x)) _clickEngine.FixedX = x;
            if (int.TryParse(TbCoordY?.Text, out int y)) _clickEngine.FixedY = y;
        }

        private void BtnPickCoord_Click(object sender, RoutedEventArgs e)
        {
            Win32Api.GetCursorPos(out var pt);
            TbCoordX.Text = pt.X.ToString();
            TbCoordY.Text = pt.Y.ToString();
            _clickEngine.FixedX = pt.X;
            _clickEngine.FixedY = pt.Y;
            RbFixed.IsChecked = true;
        }

        // ================= SEQUENCE CONTROLS =================
        private void BtnAddSeqPoint_Click(object sender, RoutedEventArgs e)
        {
            int nextId = _sequenceEngine.Points.Count + 1;
            Win32Api.GetCursorPos(out var pt);
            _sequenceEngine.Points.Add(new SequencePoint { Id = nextId, X = pt.X, Y = pt.Y, DelayMs = 150 });
        }

        private void BtnPickSeqCursor_Click(object sender, RoutedEventArgs e)
        {
            int nextId = _sequenceEngine.Points.Count + 1;
            Win32Api.GetCursorPos(out var pt);
            _sequenceEngine.Points.Add(new SequencePoint { Id = nextId, X = pt.X, Y = pt.Y, DelayMs = 150 });
        }

        private void BtnClearSeq_Click(object sender, RoutedEventArgs e)
        {
            _sequenceEngine.Points.Clear();
        }

        // ================= PIXEL CONTROLS =================
        private void BtnSamplePixel_Click(object sender, RoutedEventArgs e)
        {
            System.Drawing.Color c = PixelTriggerEngine.SamplePixelAtCursor(out int x, out int y);
            TbPixelX.Text = x.ToString();
            TbPixelY.Text = y.ToString();
            _pixelEngine.TargetX = x;
            _pixelEngine.TargetY = y;
            _pixelEngine.TargetColor = c;

            BorderPixelColorPreview.Background = new SolidColorBrush(System.Windows.Media.Color.FromRgb(c.R, c.G, c.B));
            TxtPixelHex.Text = $"#{c.R:X2}{c.G:X2}{c.B:X2}";
        }

        // ================= VISUAL BOT CONTROLS =================
        private void UpdateVisualTargetCount()
        {
            int active = _visualEngine.Targets.Count(t => t.IsEnabled);
            int total = _visualEngine.Targets.Count;
            if (TxtVisualTargetCount != null)
            {
                TxtVisualTargetCount.Text = $"TARGETS ({active} Active / {total} Total)";
            }
        }

        private void BtnVisualPasteClip_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (Clipboard.ContainsImage())
                {
                    var imgSource = Clipboard.GetImage();
                    if (imgSource != null)
                    {
                        string fileName = $"snip_{DateTimeOffset.UtcNow.ToUnixTimeSeconds()}_{_visualEngine.Targets.Count + 1}.png";
                        string filePath = Path.Combine(VisualBotEngine.TemplatesDirectory, fileName);
                        using (var fs = new FileStream(filePath, FileMode.Create))
                        {
                            BitmapEncoder enc = new PngBitmapEncoder();
                            enc.Frames.Add(BitmapFrame.Create(imgSource));
                            enc.Save(fs);
                        }

                        _visualEngine.Targets.Add(new VisualTargetItem
                        {
                            Name = fileName,
                            FilePath = filePath,
                            Width = (int)imgSource.PixelWidth,
                            Height = (int)imgSource.PixelHeight,
                            IsEnabled = true
                        });

                        UpdateVisualTargetCount();
                        TxtVisualStatus.Text = $"✅ Pasted '{fileName}' ({imgSource.PixelWidth}x{imgSource.PixelHeight}) from clipboard!";
                    }
                }
                else
                {
                    MessageBox.Show("No image found in clipboard.\n\nPress Win+Shift+S to capture a screenshot region, then click 'Paste Clipboard'.", "Paste Clipboard", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to paste image: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnVisualAddFile_Click(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "Image Files|*.png;*.jpg;*.jpeg;*.bmp|All Files|*.*",
                Title = "Select Image Template(s) to Search",
                Multiselect = true
            };
            if (dlg.ShowDialog() == true)
            {
                foreach (string file in dlg.FileNames)
                {
                    try
                    {
                        using var bmp = new System.Drawing.Bitmap(file);
                        _visualEngine.Targets.Add(new VisualTargetItem
                        {
                            Name = Path.GetFileName(file),
                            FilePath = file,
                            Width = bmp.Width,
                            Height = bmp.Height,
                            IsEnabled = true
                        });
                    }
                    catch { }
                }
                UpdateVisualTargetCount();
                TxtVisualStatus.Text = $"Loaded {dlg.FileNames.Length} template(s) into queue.";
            }
        }

        private void BtnVisualSelectAll_Click(object sender, RoutedEventArgs e)
        {
            foreach (var t in _visualEngine.Targets) t.IsEnabled = true;
            UpdateVisualTargetCount();
        }

        private void BtnVisualClearAll_Click(object sender, RoutedEventArgs e)
        {
            _visualEngine.Targets.Clear();
            UpdateVisualTargetCount();
            TxtVisualStatus.Text = "Cleared all target templates.";
        }

        private void BtnVisualDeleteTarget_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string id)
            {
                var item = _visualEngine.Targets.FirstOrDefault(t => t.Id == id);
                if (item != null)
                {
                    _visualEngine.Targets.Remove(item);
                    UpdateVisualTargetCount();
                }
            }
        }

        private void SyncVisualEngineSettings()
        {
            if (_isInitializing || SliderVisualConf == null) return;
            _visualEngine.ConfidenceThreshold = SliderVisualConf.Value / 100.0;
            if (CmbVisualAction != null)
            {
                _visualEngine.Button = CmbVisualAction.SelectedIndex == 2 ? MouseButtonType.Right : MouseButtonType.Left;
                _visualEngine.ClickType = CmbVisualAction.SelectedIndex == 1 ? ClickType.Double : ClickType.Single;
            }
            if (ChkVisualSmooth != null) _visualEngine.SmoothMovement = ChkVisualSmooth.IsChecked == true;
            if (CmbVisualSpeed != null)
            {
                _visualEngine.TravelSpeed = CmbVisualSpeed.SelectedIndex switch
                {
                    0 => CursorTravelSpeed.Fast,
                    2 => CursorTravelSpeed.Gentle,
                    _ => CursorTravelSpeed.Smooth
                };
            }
            if (TbVisualCooldown != null && double.TryParse(TbVisualCooldown.Text, out double cd)) _visualEngine.CooldownSec = Math.Max(0.0, cd);
            if (TbVisualInterval != null && double.TryParse(TbVisualInterval.Text, out double intvSec)) _visualEngine.ScanIntervalSec = Math.Max(0.01, intvSec);
            if (CmbVisualStrategy != null) _visualEngine.Strategy = CmbVisualStrategy.SelectedIndex == 1 ? VisualSelectionStrategy.ClosestToCursor : VisualSelectionStrategy.HighestConfidence;
            if (CmbVisualFlow != null) _visualEngine.FlowMode = CmbVisualFlow.SelectedIndex == 1 ? VisualFlowMode.OrderedSteps : VisualFlowMode.AnyMatch;
            if (ChkVisualLoop != null) _visualEngine.LoopQueue = ChkVisualLoop.IsChecked == true;
            if (ChkUseRegion != null) _visualEngine.UseRegion = ChkUseRegion.IsChecked == true;
            if (TbRegX != null && int.TryParse(TbRegX.Text, out int rx)) _visualEngine.RegionX = rx;
            if (TbRegY != null && int.TryParse(TbRegY.Text, out int ry)) _visualEngine.RegionY = ry;
            if (TbRegW != null && int.TryParse(TbRegW.Text, out int rw)) _visualEngine.RegionWidth = rw;
            if (TbRegH != null && int.TryParse(TbRegH.Text, out int rh)) _visualEngine.RegionHeight = rh;
        }

        private void LoadVisualSettingsFromAppConfig()
        {
            try
            {
                if (SliderVisualConf != null) SliderVisualConf.Value = _settings.VisualConfidenceThreshold * 100.0;
                if (CmbVisualAction != null) CmbVisualAction.SelectedIndex = Math.Clamp(_settings.VisualClickAction, 0, 2);
                if (ChkVisualSmooth != null) ChkVisualSmooth.IsChecked = _settings.VisualSmoothMovement;
                if (CmbVisualSpeed != null) CmbVisualSpeed.SelectedIndex = Math.Clamp(_settings.VisualTravelSpeed, 0, 2);
                if (TbVisualCooldown != null) TbVisualCooldown.Text = _settings.VisualCooldownSec.ToString("0.0");
                if (TbVisualInterval != null) TbVisualInterval.Text = _settings.VisualScanIntervalSec.ToString("0.00");
                if (CmbVisualStrategy != null) CmbVisualStrategy.SelectedIndex = Math.Clamp(_settings.VisualSelectionStrategy, 0, 1);
                if (CmbVisualFlow != null) CmbVisualFlow.SelectedIndex = Math.Clamp(_settings.VisualFlowMode, 0, 1);
                if (ChkVisualLoop != null) ChkVisualLoop.IsChecked = _settings.VisualLoopQueue;
                if (ChkUseRegion != null) ChkUseRegion.IsChecked = _settings.VisualUseRegion;
                if (TbRegX != null) TbRegX.Text = _settings.VisualRegionX.ToString();
                if (TbRegY != null) TbRegY.Text = _settings.VisualRegionY.ToString();
                if (TbRegW != null) TbRegW.Text = _settings.VisualRegionW.ToString();
                if (TbRegH != null) TbRegH.Text = _settings.VisualRegionH.ToString();

                SyncVisualEngineSettings();
            }
            catch { }
        }

        private void SaveVisualSettingsToAppConfig()
        {
            if (_isInitializing) return;
            try
            {
                _settings.VisualConfidenceThreshold = _visualEngine.ConfidenceThreshold;
                _settings.VisualClickAction = CmbVisualAction?.SelectedIndex ?? 1;
                _settings.VisualSmoothMovement = _visualEngine.SmoothMovement;
                _settings.VisualTravelSpeed = CmbVisualSpeed?.SelectedIndex ?? 1;
                _settings.VisualCooldownSec = _visualEngine.CooldownSec;
                _settings.VisualScanIntervalSec = _visualEngine.ScanIntervalSec;
                _settings.VisualSelectionStrategy = (int)_visualEngine.Strategy;
                _settings.VisualFlowMode = (int)_visualEngine.FlowMode;
                _settings.VisualLoopQueue = _visualEngine.LoopQueue;
                _settings.VisualUseRegion = _visualEngine.UseRegion;
                _settings.VisualRegionX = _visualEngine.RegionX;
                _settings.VisualRegionY = _visualEngine.RegionY;
                _settings.VisualRegionW = _visualEngine.RegionWidth;
                _settings.VisualRegionH = _visualEngine.RegionHeight;
                _settings.Save();
            }
            catch { }
        }

        private void UpdateSearchAreaOverlay()
        {
            if (_isInitializing) return;
            if (_searchAreaOverlay != null && _searchAreaOverlay.IsVisible)
            {
                _searchAreaOverlay.UpdateBounds(_visualEngine.RegionX, _visualEngine.RegionY, _visualEngine.RegionWidth, _visualEngine.RegionHeight);
            }
        }

        private void ToggleSearchAreaOverlay()
        {
            if (_isInitializing) return;
            if (_searchAreaOverlay == null)
            {
                _searchAreaOverlay = new SearchAreaWindow();
                _searchAreaOverlay.Closed += (s, e) => _searchAreaOverlay = null;
            }

            if (_searchAreaOverlay.IsVisible)
            {
                _searchAreaOverlay.Hide();
                if (BtnToggleAreaVisual != null) BtnToggleAreaVisual.Content = "👁️ Show Area Box";
            }
            else
            {
                SyncVisualEngineSettings();
                _searchAreaOverlay.UpdateBounds(_visualEngine.RegionX, _visualEngine.RegionY, _visualEngine.RegionWidth, _visualEngine.RegionHeight);
                _searchAreaOverlay.Show();
                if (BtnToggleAreaVisual != null) BtnToggleAreaVisual.Content = "🙈 Hide Area Box";
            }
        }

        private void BtnToggleAreaVisual_Click(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            ToggleSearchAreaOverlay();
        }

        private void BtnPickAreaScreen_Click(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            var picker = new RegionPickerWindow();
            picker.ShowDialog();
            if (picker.AreaSelected)
            {
                var rect = picker.SelectedRect;
                TbRegX.Text = ((int)rect.X).ToString();
                TbRegY.Text = ((int)rect.Y).ToString();
                TbRegW.Text = ((int)rect.Width).ToString();
                TbRegH.Text = ((int)rect.Height).ToString();
                ChkUseRegion.IsChecked = true;

                SyncVisualEngineSettings();
                UpdateSearchAreaOverlay();
                SaveVisualSettingsToAppConfig();
                TxtVisualStatus.Text = $"🎯 Restricted search area set to {TbRegW.Text}x{TbRegH.Text} at ({TbRegX.Text}, {TbRegY.Text})";
            }
        }

        private void ChkUseRegion_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            if (ChkUseRegion.IsChecked == true)
            {
                if (_searchAreaOverlay == null || !_searchAreaOverlay.IsVisible)
                {
                    ToggleSearchAreaOverlay();
                }
                else
                {
                    UpdateSearchAreaOverlay();
                }
            }
            else
            {
                if (_searchAreaOverlay != null && _searchAreaOverlay.IsVisible)
                {
                    ToggleSearchAreaOverlay();
                }
            }
            SaveVisualSettingsToAppConfig();
        }

        private void TbRegion_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            UpdateSearchAreaOverlay();
            SaveVisualSettingsToAppConfig();
        }

        private void TbVisualTiming_LostFocus(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void CmbVisualFlow_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void CmbVisualStrategy_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void VisualSetting_Changed(object sender, RoutedEventArgs e)
        {
            if (_isInitializing) return;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private async void BtnVisualTestClick_Click(object sender, RoutedEventArgs e)
        {
            SyncVisualEngineSettings();
            TxtVisualStatus.Text = "🔍 Searching screen...";
            BtnVisualTestClick.IsEnabled = false;
            BtnVisualScanOnly.IsEnabled = false;

            try
            {
                var res = await Task.Run(() => _visualEngine.TestAndClick());
                if (res.found)
                {
                    TxtVisualStatus.Text = $"🎯 Found & Clicked '{res.targetName}' at ({res.pos.X}, {res.pos.Y}) • Match: {res.confidence * 100:F1}%";
                }
                else
                {
                    TxtVisualStatus.Text = "❌ No active target was found on screen. Try lowering threshold or check screen.";
                }
            }
            finally
            {
                BtnVisualTestClick.IsEnabled = true;
                BtnVisualScanOnly.IsEnabled = true;
            }
        }

        private async void BtnVisualScanOnly_Click(object sender, RoutedEventArgs e)
        {
            SyncVisualEngineSettings();
            TxtVisualStatus.Text = "🔍 Scanning screen...";
            BtnVisualTestClick.IsEnabled = false;
            BtnVisualScanOnly.IsEnabled = false;

            try
            {
                var res = await Task.Run(() => _visualEngine.TestScan());
                if (res.found)
                {
                    TxtVisualStatus.Text = $"🔍 Found '{res.targetName}' at ({res.pos.X}, {res.pos.Y}) • Match: {res.confidence * 100:F1}% (Scan only, not clicked)";
                }
                else
                {
                    TxtVisualStatus.Text = "❌ No active target was found on screen.";
                }
            }
            finally
            {
                BtnVisualTestClick.IsEnabled = true;
                BtnVisualScanOnly.IsEnabled = true;
            }
        }

        private void LoadVisualPresetsCombo()
        {
            var presets = VisualBotEngine.GetAvailablePresets();
            CmbVisualPresets.ItemsSource = presets;
            if (presets.Count > 0)
            {
                CmbVisualPresets.SelectedIndex = 0;
            }
        }

        private void BtnVisualSavePreset_Click(object sender, RoutedEventArgs e)
        {
            SyncVisualEngineSettings();
            string presetName = CmbVisualPresets.Text?.Trim() ?? "";
            if (string.IsNullOrWhiteSpace(presetName))
            {
                presetName = "Preset_1";
            }
            _visualEngine.SaveToPreset(presetName);
            LoadVisualPresetsCombo();
            CmbVisualPresets.SelectedItem = presetName;
            _settings.LastVisualPreset = presetName;
            SaveVisualSettingsToAppConfig();
            TxtVisualStatus.Text = $"💾 Preset '{presetName}' saved successfully!";
        }

        private void BtnVisualLoadPreset_Click(object sender, RoutedEventArgs e)
        {
            string presetName = CmbVisualPresets.Text?.Trim() ?? "";
            if (!string.IsNullOrWhiteSpace(presetName) && _visualEngine.LoadFromPreset(presetName))
            {
                SliderVisualConf.Value = _visualEngine.ConfidenceThreshold * 100.0;
                CmbVisualAction.SelectedIndex = _visualEngine.ClickType == ClickType.Double ? 1 : (_visualEngine.Button == MouseButtonType.Right ? 2 : 0);
                ChkVisualSmooth.IsChecked = _visualEngine.SmoothMovement;
                CmbVisualSpeed.SelectedIndex = _visualEngine.TravelSpeed switch
                {
                    CursorTravelSpeed.Fast => 0,
                    CursorTravelSpeed.Gentle => 2,
                    _ => 1
                };
                TbVisualCooldown.Text = _visualEngine.CooldownSec.ToString("0.0");
                TbVisualInterval.Text = _visualEngine.ScanIntervalSec.ToString("0.00");
                if (CmbVisualStrategy != null) CmbVisualStrategy.SelectedIndex = (int)_visualEngine.Strategy;
                CmbVisualFlow.SelectedIndex = (int)_visualEngine.FlowMode;
                ChkVisualLoop.IsChecked = _visualEngine.LoopQueue;
                ChkUseRegion.IsChecked = _visualEngine.UseRegion;
                TbRegX.Text = _visualEngine.RegionX.ToString();
                TbRegY.Text = _visualEngine.RegionY.ToString();
                TbRegW.Text = _visualEngine.RegionWidth.ToString();
                TbRegH.Text = _visualEngine.RegionHeight.ToString();

                UpdateVisualTargetCount();
                UpdateSearchAreaOverlay();
                SaveVisualSettingsToAppConfig();
                TxtVisualStatus.Text = $"📂 Loaded preset '{presetName}' ({_visualEngine.Targets.Count} targets)!";
            }
        }

        private void BtnVisualDeletePreset_Click(object sender, RoutedEventArgs e)
        {
            string presetName = CmbVisualPresets.Text?.Trim() ?? "";
            if (!string.IsNullOrWhiteSpace(presetName))
            {
                string path = Path.Combine(VisualBotEngine.PresetsDirectory, $"{presetName}.json");
                if (File.Exists(path))
                {
                    File.Delete(path);
                    LoadVisualPresetsCombo();
                    TxtVisualStatus.Text = $"🗑️ Preset '{presetName}' deleted.";
                }
            }
        }

        private void BtnPrecisionExact_Click(object sender, RoutedEventArgs e)
        {
            SliderVisualConf.Value = 95;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void BtnPrecisionSimilar_Click(object sender, RoutedEventArgs e)
        {
            SliderVisualConf.Value = 60;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void BtnPrecisionClosest_Click(object sender, RoutedEventArgs e)
        {
            SliderVisualConf.Value = 45;
            SyncVisualEngineSettings();
            SaveVisualSettingsToAppConfig();
        }

        private void SliderVisualConf_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (_isInitializing || TxtVisualConfVal == null) return;
            double val = Math.Round(e.NewValue);
            string mode = val >= 90 ? "(Exact)" : (val <= 50 ? "(Closest)" : "(Similar)");
            TxtVisualConfVal.Text = $"{val}% {mode}";
            _visualEngine.ConfidenceThreshold = val / 100.0;
            SaveVisualSettingsToAppConfig();
        }

        // ================= MACRO CONTROLS =================
        private void BtnMacroRecord_Click(object sender, RoutedEventArgs e)
        {
            _macroEngine.ToggleRecording();
        }

        private void BtnMacroPlay_Click(object sender, RoutedEventArgs e)
        {
            _macroEngine.TogglePlayback();
        }

        // ================= THEME SWITCHER =================
        private void ThemeBtn_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string themeName)
            {
                _settings.Theme = themeName;
                ThemeManager.ApplyTheme(this, themeName);
                if (_overlayWindow != null)
                {
                    ThemeManager.ApplyTheme(_overlayWindow, themeName);
                }
                _settings.Save();

                if (TxtActiveTheme != null)
                {
                    TxtActiveTheme.Text = $"Active Theme: {themeName}";
                }
                RefreshNavButtons();
            }
        }

        // ================= COMPACT OVERLAY MODE =================
        private void BtnCompactMode_Click(object sender, RoutedEventArgs e)
        {
            ToggleCompactMode();
        }

        public void SwitchToCompactMode()
        {
            if (_overlayWindow == null)
            {
                _overlayWindow = new OverlayWindow(this, _settings);
            }

            ThemeManager.ApplyTheme(_overlayWindow, _settings.Theme);
            long clicks = long.TryParse(TxtClicks.Text.Replace(",", ""), out var c) ? c : 0;
            double cps = double.TryParse(TxtCps.Text.Replace(" CPS", ""), out var s) ? s : 0;
            _overlayWindow.UpdateStats(clicks, cps, IsAnyEngineRunning(), GetActiveEngineName());

            this.Hide();
            _overlayWindow.Show();
        }

        public void SwitchToFullMode()
        {
            if (_overlayWindow != null)
            {
                _settings.OverlayX = _overlayWindow.Left;
                _settings.OverlayY = _overlayWindow.Top;
                _settings.Save();
                _overlayWindow.Hide();
            }

            this.Show();
            this.WindowState = WindowState.Normal;
            this.Activate();
        }

        public void ToggleCompactMode()
        {
            if (this.IsVisible)
            {
                SwitchToCompactMode();
            }
            else
            {
                SwitchToFullMode();
            }
        }

        public string GetActiveEngineName()
        {
            return _activeTabKey switch
            {
                "sequence" => "Sequence",
                "pixel" => "Pixel",
                "visual" => "Visual",
                "keyspam" => "KeySpam",
                "macro" => "Macro",
                _ => "Burst"
            };
        }

        // ================= MODULE SELECTOR =================
        private void SyncModuleCheckboxes()
        {
            ModBurst.IsChecked = _settings.ShowBurst;
            ModSequence.IsChecked = _settings.ShowSequence;
            ModPixel.IsChecked = _settings.ShowPixelTrigger;
            ModVisual.IsChecked = _settings.ShowVisualBot;
            ModKeySpam.IsChecked = _settings.ShowKeySpammer;
            ModMacro.IsChecked = _settings.ShowMacroStudio;
        }

        private void ModuleToggle_Changed(object sender, RoutedEventArgs e)
        {
            _settings.ShowBurst = ModBurst.IsChecked == true;
            _settings.ShowSequence = ModSequence.IsChecked == true;
            _settings.ShowPixelTrigger = ModPixel.IsChecked == true;
            _settings.ShowVisualBot = ModVisual.IsChecked == true;
            _settings.ShowKeySpammer = ModKeySpam.IsChecked == true;
            _settings.ShowMacroStudio = ModMacro.IsChecked == true;
            _settings.Save();

            ApplyModuleVisibility();
        }

        private void ApplyModuleVisibility()
        {
            NavBurst.Visibility = _settings.ShowBurst ? Visibility.Visible : Visibility.Collapsed;
            NavSequence.Visibility = _settings.ShowSequence ? Visibility.Visible : Visibility.Collapsed;
            NavPixel.Visibility = _settings.ShowPixelTrigger ? Visibility.Visible : Visibility.Collapsed;
            NavVisual.Visibility = _settings.ShowVisualBot ? Visibility.Visible : Visibility.Collapsed;
            NavKeySpam.Visibility = _settings.ShowKeySpammer ? Visibility.Visible : Visibility.Collapsed;
            NavMacro.Visibility = _settings.ShowMacroStudio ? Visibility.Visible : Visibility.Collapsed;
        }

        // ================= NAVIGATION =================
        private void NavBurst_Click(object sender, RoutedEventArgs e) => SetPage("burst", ViewBurst, NavBurst);
        private void NavSequence_Click(object sender, RoutedEventArgs e) => SetPage("sequence", ViewSequence, NavSequence);
        private void NavPixel_Click(object sender, RoutedEventArgs e) => SetPage("pixel", ViewPixel, NavPixel);
        private void NavVisual_Click(object sender, RoutedEventArgs e) => SetPage("visual", ViewVisual, NavVisual);
        private void NavKeySpam_Click(object sender, RoutedEventArgs e) => SetPage("keyspam", ViewKeySpam, NavKeySpam);
        private void NavMacro_Click(object sender, RoutedEventArgs e) => SetPage("macro", ViewMacro, NavMacro);
        private void NavSettings_Click(object sender, RoutedEventArgs e) => SetPage("settings", ViewSettings, NavSettings);

        private void RefreshNavButtons()
        {
            var primaryColor = (System.Windows.Media.Brush?)Resources["ColorTextPrimary"] ?? (System.Windows.Media.Brush?)Application.Current?.Resources["ColorTextPrimary"] ?? System.Windows.Media.Brushes.White;
            var accentColor = (System.Windows.Media.Brush?)Resources["ColorAccent"] ?? (System.Windows.Media.Brush?)Application.Current?.Resources["ColorAccent"] ?? System.Windows.Media.Brushes.DodgerBlue;
            var borderColor = (System.Windows.Media.Brush?)Resources["ColorBorder"] ?? (System.Windows.Media.Brush?)Application.Current?.Resources["ColorBorder"] ?? System.Windows.Media.Brushes.Gray;

            Button currentBtn = _activeTabKey switch
            {
                "burst" => NavBurst,
                "sequence" => NavSequence,
                "pixel" => NavPixel,
                "visual" => NavVisual,
                "keyspam" => NavKeySpam,
                "macro" => NavMacro,
                "settings" => NavSettings,
                _ => NavBurst
            };

            foreach (var b in new[] { NavBurst, NavSequence, NavPixel, NavVisual, NavKeySpam, NavMacro, NavSettings })
            {
                b.Background = System.Windows.Media.Brushes.Transparent;
                b.Foreground = primaryColor;
                b.FontWeight = FontWeights.Normal;
            }

            currentBtn.Background = borderColor;
            currentBtn.Foreground = accentColor;
            currentBtn.FontWeight = FontWeights.Bold;
        }

        private void SetPage(string key, ScrollViewer targetView, Button activeBtn)
        {
            _activeTabKey = key;

            ViewBurst.Visibility = Visibility.Collapsed;
            ViewSequence.Visibility = Visibility.Collapsed;
            ViewPixel.Visibility = Visibility.Collapsed;
            ViewVisual.Visibility = Visibility.Collapsed;
            ViewKeySpam.Visibility = Visibility.Collapsed;
            ViewMacro.Visibility = Visibility.Collapsed;
            ViewSettings.Visibility = Visibility.Collapsed;

            targetView.Visibility = Visibility.Visible;

            RefreshNavButtons();
        }
    }
}
