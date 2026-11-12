using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using ApexClicker.Native;

namespace ApexClicker
{
    public class SearchAreaWindow : Window
    {
        private readonly TextBlock _label;
        private readonly Border _mainBorder;
        private int _lastX = 100;
        private int _lastY = 100;
        private int _lastW = 400;
        private int _lastH = 300;

        public SearchAreaWindow()
        {
            WindowStyle = WindowStyle.None;
            AllowsTransparency = true;
            Background = Brushes.Transparent;
            Topmost = true;
            ShowInTaskbar = false;
            IsHitTestVisible = false; // Click-through so user can still interact with everything
            WindowStartupLocation = WindowStartupLocation.Manual;

            _mainBorder = new Border
            {
                BorderBrush = new SolidColorBrush(Color.FromArgb(235, 137, 180, 250)), // Vibrant accent blue
                BorderThickness = new Thickness(2),
                CornerRadius = new CornerRadius(4),
                Background = new SolidColorBrush(Color.FromArgb(32, 137, 180, 250)) // 12% translucent fill
            };

            var badge = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(230, 24, 24, 37)),
                BorderBrush = new SolidColorBrush(Color.FromArgb(235, 137, 180, 250)),
                BorderThickness = new Thickness(0, 0, 1, 1),
                CornerRadius = new CornerRadius(0, 0, 6, 0),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Top,
                Padding = new Thickness(8, 3, 8, 3)
            };

            _label = new TextBlock
            {
                Text = "🔍 Search Area: 400x300 (X:100, Y:100)",
                FontSize = 11,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(Color.FromRgb(137, 180, 250))
            };

            badge.Child = _label;
            _mainBorder.Child = badge;
            Content = _mainBorder;

            Loaded += (s, e) => ApplyPhysicalBounds();
        }

        public void UpdateBounds(int x, int y, int w, int h)
        {
            _lastX = x;
            _lastY = y;
            _lastW = Math.Max(50, w);
            _lastH = Math.Max(35, h);
            _label.Text = $"🔍 Search Area: {_lastW}x{_lastH} (X:{_lastX}, Y:{_lastY})";

            ApplyPhysicalBounds();
        }

        private void ApplyPhysicalBounds()
        {
            if (_lastW <= 0 || _lastH <= 0) return;

            var source = PresentationSource.FromVisual(this);
            double scaleX = source?.CompositionTarget?.TransformToDevice.M11 ?? 1.0;
            double scaleY = source?.CompositionTarget?.TransformToDevice.M22 ?? 1.0;
            if (scaleX <= 0) scaleX = 1.0;
            if (scaleY <= 0) scaleY = 1.0;

            Left = _lastX / scaleX;
            Top = _lastY / scaleY;
            Width = _lastW / scaleX;
            Height = _lastH / scaleY;

            var helper = new WindowInteropHelper(this);
            if (helper.Handle != IntPtr.Zero)
            {
                Win32Api.SetWindowPos(helper.Handle, Win32Api.HWND_TOPMOST, _lastX, _lastY, _lastW, _lastH, Win32Api.SWP_NOACTIVATE | Win32Api.SWP_SHOWWINDOW);
            }
        }
    }
}
