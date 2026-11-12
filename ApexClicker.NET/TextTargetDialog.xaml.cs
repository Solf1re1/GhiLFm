using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using ApexClicker.Core;

namespace ApexClicker
{
    public partial class TextTargetDialog : Window
    {
        public VisualTargetItem? CreatedTarget { get; private set; }
        private bool _customNameEdited;

        public TextTargetDialog()
        {
            InitializeComponent();
            Loaded += (s, e) => TbTextToMatch.Focus();
            TbTargetName.TextChanged += (s, e) =>
            {
                if (TbTargetName.IsKeyboardFocused)
                {
                    _customNameEdited = true;
                }
            };
        }

        private void TitleBar_MouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                DragMove();
            }
        }

        private void TbTextToMatch_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (!_customNameEdited && TbTargetName != null)
            {
                string text = TbTextToMatch.Text?.Trim() ?? "";
                TbTargetName.Text = string.IsNullOrEmpty(text) ? "Text Target" : $"Text: {text}";
            }
        }

        private void Pill_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Content is string word)
            {
                TbTextToMatch.Text = word;
                TbTextToMatch.CaretIndex = word.Length;
                TbTextToMatch.Focus();
            }
        }

        private void EngineMode_Changed(object sender, RoutedEventArgs e)
        {
            if (PanelOcrOptions == null || PanelTemplateOptions == null) return;

            bool isOcr = RbOcr.IsChecked == true;
            PanelOcrOptions.Visibility = isOcr ? Visibility.Visible : Visibility.Collapsed;
            PanelTemplateOptions.Visibility = isOcr ? Visibility.Collapsed : Visibility.Visible;
        }

        private void TemplateOption_Changed(object sender, RoutedEventArgs e)
        {
        }

        private void BtnAddTarget_Click(object sender, RoutedEventArgs e)
        {
            string matchText = TbTextToMatch.Text?.Trim() ?? "";
            if (string.IsNullOrWhiteSpace(matchText))
            {
                MessageBox.Show("Please enter the text or word to search for.", "Missing Text", MessageBoxButton.OK, MessageBoxImage.Warning);
                TbTextToMatch.Focus();
                return;
            }

            string targetName = TbTargetName.Text?.Trim() ?? "";
            if (string.IsNullOrWhiteSpace(targetName))
            {
                targetName = $"Text: {matchText}";
            }

            bool isOcr = RbOcr.IsChecked == true;
            string targetId = Guid.NewGuid().ToString("N")[..8];

            if (isOcr)
            {
                // Generate a visual preview thumbnail for the OCR target
                string previewFile = Path.Combine(VisualBotEngine.TemplatesDirectory, $"ocr_{targetId}.png");
                try
                {
                    using var previewBmp = VisualBotEngine.GenerateTextTemplate(matchText, "Segoe UI", 16, true, System.Drawing.Color.White, System.Drawing.Color.FromArgb(49, 50, 68));
                    previewBmp.Save(previewFile, ImageFormat.Png);
                }
                catch { }

                CreatedTarget = new VisualTargetItem
                {
                    Id = targetId,
                    Name = targetName,
                    TargetType = VisualTargetType.TextOcr,
                    TargetText = matchText,
                    ExactWordMatch = ChkExactWord.IsChecked == true,
                    CaseSensitive = ChkCaseSensitive.IsChecked == true,
                    FilePath = previewFile,
                    Width = 64,
                    Height = 24,
                    IsEnabled = true
                };
            }
            else
            {
                // Pre-rendered template mode
                string fontFamily = ((ComboBoxItem)CmbFontFamily.SelectedItem)?.Content?.ToString() ?? "Segoe UI";
                int fontSize = 16;
                if (int.TryParse(((ComboBoxItem)CmbFontSize.SelectedItem)?.Content?.ToString(), out int parsedSize))
                {
                    fontSize = parsedSize;
                }
                bool bold = ChkFontBold.IsChecked == true;

                string tplFile = Path.Combine(VisualBotEngine.TemplatesDirectory, $"tpl_{targetId}.png");
                using var tplBmp = VisualBotEngine.GenerateTextTemplate(matchText, fontFamily, fontSize, bold, System.Drawing.Color.White, null);
                tplBmp.Save(tplFile, ImageFormat.Png);

                CreatedTarget = new VisualTargetItem
                {
                    Id = targetId,
                    Name = targetName,
                    TargetType = VisualTargetType.TextTemplate,
                    TargetText = matchText,
                    FilePath = tplFile,
                    Width = tplBmp.Width,
                    Height = tplBmp.Height,
                    IsEnabled = true
                };
            }

            DialogResult = true;
            Close();
        }

        private void BtnCancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
