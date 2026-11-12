using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using ApexClicker.Native;

namespace ApexClicker
{
    public class RegionPickerWindow : Window
    {
        private Point _startCanvasPoint;
        private Win32Api.POINT _startScreenPoint;
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
                    _startCanvasPoint = e.GetPosition(_canvas);
                    Win32Api.GetCursorPos(out _startScreenPoint);

                    Canvas.SetLeft(_selectionRect, _startCanvasPoint.X);
                    Canvas.SetTop(_selectionRect, _startCanvasPoint.Y);
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
                    var curCanvas = e.GetPosition(_canvas);
                    double vx = Math.Min(_startCanvasPoint.X, curCanvas.X);
                    double vy = Math.Min(_startCanvasPoint.Y, curCanvas.Y);
                    double vw = Math.Abs(curCanvas.X - _startCanvasPoint.X);
                    double vh = Math.Abs(curCanvas.Y - _startCanvasPoint.Y);

                    Canvas.SetLeft(_selectionRect, vx);
                    Canvas.SetTop(_selectionRect, vy);
                    _selectionRect.Width = vw;
                    _selectionRect.Height = vh;

                    Win32Api.GetCursorPos(out var curScreen);
                    int physW = Math.Abs(curScreen.X - _startScreenPoint.X);
                    int physH = Math.Abs(curScreen.Y - _startScreenPoint.Y);
                    int physX = Math.Min(_startScreenPoint.X, curScreen.X);
                    int physY = Math.Min(_startScreenPoint.Y, curScreen.Y);
                    _infoText.Text = $"Selected Region: {physW} x {physH} px  (X: {physX}, Y: {physY})";
                }
            };

            MouseUp += (s, e) =>
            {
                if (_isDragging)
                {
                    _isDragging = false;
                    ReleaseMouseCapture();

                    Win32Api.GetCursorPos(out var screenEnd);
                    int physX = Math.Min(_startScreenPoint.X, screenEnd.X);
                    int physY = Math.Min(_startScreenPoint.Y, screenEnd.Y);
                    int physW = Math.Abs(screenEnd.X - _startScreenPoint.X);
                    int physH = Math.Abs(screenEnd.Y - _startScreenPoint.Y);

                    if (physW > 15 && physH > 15)
                    {
                        SelectedRect = new Rect(physX, physY, physW, physH);
                        AreaSelected = true;
                    }
                    Close();
                }
            };
        }
    }
}
