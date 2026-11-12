using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace ApexClicker
{
    public class SearchAreaWindow : Window
    {
        private readonly TextBlock _label;
        private readonly Border _mainBorder;

        public SearchAreaWindow()
        {
            WindowStyle = WindowStyle.None;
            AllowsTransparency = true;
            Background = Brushes.Transparent;
            Topmost = true;
            ShowInTaskbar = false;
            IsHitTestVisible = false; // Click-through so user can still interact with everything

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
        }

        public void UpdateBounds(int x, int y, int w, int h)
        {
            Left = x;
            Top = y;
            Width = Math.Max(50, w);
            Height = Math.Max(35, h);
            _label.Text = $"🔍 Search Area: {w}x{h} (X:{x}, Y:{y})";
        }
    }
}
