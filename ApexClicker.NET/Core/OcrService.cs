using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage.Streams;

namespace ApexClicker.Core
{
    public struct TextMatchResult
    {
        public string MatchedText;
        public Rectangle Bounds;
        public int CenterX => Bounds.X + Bounds.Width / 2;
        public int CenterY => Bounds.Y + Bounds.Height / 2;
        public double Confidence;
    }

    public static class OcrService
    {
        private static OcrEngine? _engine;
        private static bool _initialized;
        private static readonly object _lock = new();

        public static bool IsAvailable
        {
            get
            {
                EnsureInitialized();
                return _engine != null;
            }
        }

        private static void EnsureInitialized()
        {
            if (_initialized) return;
            lock (_lock)
            {
                if (_initialized) return;
                _initialized = true;

                try
                {
                    _engine = OcrEngine.TryCreateFromUserProfileLanguages();
                    if (_engine == null)
                    {
                        _engine = OcrEngine.TryCreateFromLanguage(new Windows.Globalization.Language("en-US"));
                    }
                }
                catch
                {
                    _engine = null;
                }
            }
        }

        public static async Task<SoftwareBitmap> BitmapToSoftwareBitmapAsync(Bitmap bmp)
        {
            using var ms = new MemoryStream();
            bmp.Save(ms, ImageFormat.Bmp);
            ms.Position = 0;

            var ras = new InMemoryRandomAccessStream();
            using (var writeStream = ras.AsStreamForWrite())
            {
                await ms.CopyToAsync(writeStream);
                await writeStream.FlushAsync();
            }
            ras.Seek(0);

            var decoder = await BitmapDecoder.CreateAsync(ras);
            return await decoder.GetSoftwareBitmapAsync();
        }

        public static async Task<OcrResult?> RecognizeAsync(Bitmap bmp)
        {
            EnsureInitialized();
            if (_engine == null) return null;

            try
            {
                using var softwareBitmap = await BitmapToSoftwareBitmapAsync(bmp);
                return await _engine.RecognizeAsync(softwareBitmap);
            }
            catch
            {
                return null;
            }
        }

        public static List<TextMatchResult> FindText(
            Bitmap bmp,
            string query,
            bool exactWordMatch = false,
            bool caseSensitive = false,
            int screenOffsetX = 0,
            int screenOffsetY = 0)
        {
            try
            {
                var task = RecognizeAsync(bmp);
                task.Wait(1500); // 1.5s max timeout for safety
                if (!task.IsCompletedSuccessfully || task.Result == null) return new List<TextMatchResult>();

                return ParseOcrResults(task.Result, query, exactWordMatch, caseSensitive, screenOffsetX, screenOffsetY);
            }
            catch
            {
                return new List<TextMatchResult>();
            }
        }

        public static List<TextMatchResult> ParseOcrResults(
            OcrResult result,
            string query,
            bool exactWordMatch = false,
            bool caseSensitive = false,
            int screenOffsetX = 0,
            int screenOffsetY = 0)
        {
            var matches = new List<TextMatchResult>();
            if (result == null || string.IsNullOrWhiteSpace(query)) return matches;

            string cleanQuery = query.Trim();
            var comparison = caseSensitive ? StringComparison.Ordinal : StringComparison.OrdinalIgnoreCase;

            foreach (var line in result.Lines)
            {
                string lineText = line.Text;
                int phraseIndex = lineText.IndexOf(cleanQuery, comparison);

                if (phraseIndex >= 0)
                {
                    // Find words intersecting this query phrase
                    var matchedWords = new List<OcrWord>();
                    int cursor = 0;
                    foreach (var word in line.Words)
                    {
                        int wordStart = lineText.IndexOf(word.Text, cursor, comparison);
                        if (wordStart < 0) wordStart = cursor;
                        int wordEnd = wordStart + word.Text.Length;
                        cursor = wordEnd;

                        if (wordStart <= phraseIndex + cleanQuery.Length && wordEnd >= phraseIndex)
                        {
                            matchedWords.Add(word);
                        }
                    }

                    if (matchedWords.Count > 0)
                    {
                        double minX = matchedWords.Min(w => w.BoundingRect.X);
                        double minY = matchedWords.Min(w => w.BoundingRect.Y);
                        double maxX = matchedWords.Max(w => w.BoundingRect.X + w.BoundingRect.Width);
                        double maxY = matchedWords.Max(w => w.BoundingRect.Y + w.BoundingRect.Height);

                        matches.Add(new TextMatchResult
                        {
                            MatchedText = cleanQuery,
                            Bounds = new Rectangle(
                                screenOffsetX + (int)minX,
                                screenOffsetY + (int)minY,
                                (int)(maxX - minX),
                                (int)(maxY - minY)),
                            Confidence = 0.95
                        });
                        continue;
                    }
                }

                // Check individual words
                foreach (var word in line.Words)
                {
                    bool isWordMatch = exactWordMatch
                        ? string.Equals(word.Text, cleanQuery, comparison)
                        : word.Text.Contains(cleanQuery, comparison);

                    if (isWordMatch)
                    {
                        matches.Add(new TextMatchResult
                        {
                            MatchedText = word.Text,
                            Bounds = new Rectangle(
                                screenOffsetX + (int)word.BoundingRect.X,
                                screenOffsetY + (int)word.BoundingRect.Y,
                                (int)word.BoundingRect.Width,
                                (int)word.BoundingRect.Height),
                            Confidence = 0.95
                        });
                    }
                }
            }

            return matches;
        }
    }
}
