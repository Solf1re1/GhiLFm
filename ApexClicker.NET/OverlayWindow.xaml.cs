using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using ApexClicker.Core;

namespace ApexClicker
{
    public partial class OverlayWindow : Window
    {
        private readonly MainWindow _mainWindow;
        private readonly AppSettings _settings;

        public OverlayWindow(MainWindow mainWindow, AppSettings settings)
        {
            InitializeComponent();
            _mainWindow = mainWindow;
            _settings = settings;

            Loaded += OverlayWindow_Loaded;
        }

        private void OverlayWindow_Loaded(object sender, RoutedEventArgs e)
        {
            if (_settings.OverlayX.HasValue && _settings.OverlayY.HasValue)
            {
                Left = _settings.OverlayX.Value;
                Top = _settings.OverlayY.Value;
            }
            else
            {
                var workArea = SystemParameters.WorkArea;
                Left = workArea.Right - Width - 30;
                Top = workArea.Top + 30;
            }
        }

        private void Border_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                DragMove();
                _settings.OverlayX = Left;
                _settings.OverlayY = Top;
                _settings.Save();
            }
        }

        private void BtnOverlayToggle_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.HandleMasterToggle();
        }

        private void BtnExpand_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.SwitchToFullMode();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            _mainWindow.SwitchToFullMode();
        }

        public void UpdateStats(long totalClicks, double currentCps, bool isRunning, string modeName)
        {
            Dispatcher.InvokeAsync(() =>
            {
                TxtOverlayClicks.Text = $"{totalClicks:N0} clicks";
                TxtOverlayCps.Text = $"{Math.Round(currentCps)} CPS";
                TxtOverlayMode.Text = modeName;

                var successBrush = (Brush?)FindResource("ColorSuccess") ?? Brushes.Green;
                var dangerBrush = (Brush?)FindResource("ColorDanger") ?? Brushes.Red;

                if (isRunning)
                {
                    TxtOverlayStatus.Text = "ACTIVE";
                    TxtOverlayStatus.Foreground = successBrush;
                    BtnOverlayToggle.Content = "⏹️";
                    BtnOverlayToggle.Background = dangerBrush;
                }
                else
                {
                    TxtOverlayStatus.Text = "STOPPED";
                    TxtOverlayStatus.Foreground = dangerBrush;
                    BtnOverlayToggle.Content = "▶️";
                    BtnOverlayToggle.Background = successBrush;
                }
            });
        }
    }
}
