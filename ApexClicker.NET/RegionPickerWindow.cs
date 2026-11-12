using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;

namespace ApexClicker
{
    public class RegionPickerWindow : Window
    {
        private Point _startPoint;
        private bool _isDragging;
        private readonly Canvas _canvas;
        private readonly Rectangle _selectionRect;
        private readonly TextBlock _infoText;
        public Rect SelectedRect { get; private set; }
        public bool AreaSelected { get; private set; }

        public RegionPickerWindow()
        {
            WindowStyle = WindowStyle.None;
            AllowsTransparency = true;
            Background = new SolidColorBrush(Color.FromArgb(50, 0, 0, 0)); // Dim overlay
            Topmost = true;
            ShowInTaskbar = false;
            Cursor = Cursors.Cross;

            Left = SystemParameters.VirtualScreenLeft;
            Top = SystemParameters.VirtualScreenTop;
            Width = SystemParameters.VirtualScreenWidth;
            Height = SystemParameters.VirtualScreenHeight;

            _canvas = new Canvas();

            _infoText = new TextBlock
            {
                Text = "🎯 Click & drag to select restricted search region  •  Press ESC to cancel",
                FontSize = 14,
                FontWeight = FontWeights.Bold,
                Foreground = Brushes.White,
                Background = new SolidColorBrush(Color.FromArgb(220, 24, 24, 37)),
                Padding = new Thickness(16, 8, 16, 8)
            };
            Canvas.SetLeft(_infoText, Math.Max(20, (Width / 2) - 250));
            Canvas.SetTop(_infoText, 40);
            _canvas.Children.Add(_infoText);

            _selectionRect = new Rectangle
            {
                Stroke = new SolidColorBrush(Color.FromRgb(137, 180, 250)),
                StrokeThickness = 2,
                Fill = new SolidColorBrush(Color.FromArgb(50, 137, 180, 250)),
                Visibility = Visibility.Collapsed
            };
            _canvas.Children.Add(_selectionRect);

            Content = _canvas;

            KeyDown += (s, e) =>
            {
                if (e.Key == Key.Escape)
                {
                    AreaSelected = false;
                    Close();
                }
            };

            MouseDown += (s, e) =>
            {
                if (e.LeftButton == MouseButtonState.Pressed)
                {
                    _isDragging = true;
                    _startPoint = e.GetPosition(_canvas);
                    Canvas.SetLeft(_selectionRect, _startPoint.X);
                    Canvas.SetTop(_selectionRect, _startPoint.Y);
                    _selectionRect.Width = 0;
                    _selectionRect.Height = 0;
                    _selectionRect.Visibility = Visibility.Visible;
                    CaptureMouse();
                }
            };

            MouseMove += (s, e) =>
            {
                if (_isDragging)
                {
                    var cur = e.GetPosition(_canvas);
                    double x = Math.Min(_startPoint.X, cur.X);
                    double y = Math.Min(_startPoint.Y, cur.Y);
                    double w = Math.Abs(cur.X - _startPoint.X);
                    double h = Math.Abs(cur.Y - _startPoint.Y);

                    Canvas.SetLeft(_selectionRect, x);
                    Canvas.SetTop(_selectionRect, y);
                    _selectionRect.Width = w;
                    _selectionRect.Height = h;
                    _infoText.Text = $"Selected Region: {Math.Round(w)} x {Math.Round(h)} px  (X: {Math.Round(x)}, Y: {Math.Round(y)})";
                }
            };

            MouseUp += (s, e) =>
            {
                if (_isDragging)
                {
                    _isDragging = false;
                    ReleaseMouseCapture();

                    var cur = e.GetPosition(_canvas);
                    double x = Math.Min(_startPoint.X, cur.X);
                    double y = Math.Min(_startPoint.Y, cur.Y);
                    double w = Math.Abs(cur.X - _startPoint.X);
                    double h = Math.Abs(cur.Y - _startPoint.Y);

                    if (w > 15 && h > 15)
                    {
                        SelectedRect = new Rect(x, y, w, h);
                        AreaSelected = true;
                    }
                    Close();
                }
            };
        }
    }
}
