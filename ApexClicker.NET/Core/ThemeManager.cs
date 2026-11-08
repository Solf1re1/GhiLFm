using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Media;

namespace ApexClicker.Core
{
    public class ThemePalette
    {
        public string Name { get; set; } = "Obsidian";
        public Color WindowBg { get; set; }
        public Color SidebarBg { get; set; }
        public Color CardBg { get; set; }
        public Color BorderColor { get; set; }
        public Color TextPrimary { get; set; }
        public Color TextSecondary { get; set; }
        public Color AccentColor { get; set; }
        public Color SuccessColor { get; set; }
        public Color DangerColor { get; set; }
    }

    public static class ThemeManager
    {
        public static readonly Dictionary<string, ThemePalette> Themes = new(StringComparer.OrdinalIgnoreCase)
        {
            ["Obsidian"] = new ThemePalette
            {
                Name = "Obsidian",
                WindowBg = Color.FromRgb(0x0D, 0x0D, 0x12),       // Deep matte obsidian
                SidebarBg = Color.FromRgb(0x08, 0x08, 0x0C),      // Charcoal sidebar
                CardBg = Color.FromRgb(0x15, 0x15, 0x1C),         // Slate obsidian cards
                BorderColor = Color.FromRgb(0x25, 0x25, 0x30),    // Subtle graphite border
                TextPrimary = Color.FromRgb(0xED, 0xED, 0xF2),    // Crisp pale grey
                TextSecondary = Color.FromRgb(0x82, 0x82, 0x92),  // Charcoal secondary
                AccentColor = Color.FromRgb(0xA8, 0x55, 0xF7),    // Obsidian Violet / Amethyst
                SuccessColor = Color.FromRgb(0x10, 0xB9, 0x81),   // Emerald green
                DangerColor = Color.FromRgb(0xF4, 0x3F, 0x5E)     // Rose red
            },
            ["Onyx"] = new ThemePalette
            {
                Name = "Onyx",
                WindowBg = Color.FromRgb(0x00, 0x00, 0x00),       // Pure AMOLED 100% Black
                SidebarBg = Color.FromRgb(0x05, 0x05, 0x05),      // Pitch graphite
                CardBg = Color.FromRgb(0x0C, 0x0C, 0x0E),         // Deep carbon card
                BorderColor = Color.FromRgb(0x1F, 0x1F, 0x24),    // Sleek border
                TextPrimary = Color.FromRgb(0xFF, 0xFF, 0xFF),    // Pure white
                TextSecondary = Color.FromRgb(0x88, 0x88, 0x88),  // Neutral grey
                AccentColor = Color.FromRgb(0xF5, 0x9E, 0x0B),    // Luxury Amber Gold
                SuccessColor = Color.FromRgb(0x22, 0xC5, 0x5E),   // Vivid green
                DangerColor = Color.FromRgb(0xEF, 0x44, 0x44)     // Crimson
            },
            ["Catppuccin"] = new ThemePalette
            {
                Name = "Catppuccin",
                WindowBg = Color.FromRgb(0x18, 0x18, 0x25),       // Mocha Base
                SidebarBg = Color.FromRgb(0x11, 0x11, 0x1B),      // Mocha Mantle
                CardBg = Color.FromRgb(0x1E, 0x1E, 0x2E),         // Mocha Surface0
                BorderColor = Color.FromRgb(0x31, 0x32, 0x44),    // Mocha Surface1
                TextPrimary = Color.FromRgb(0xCD, 0xD6, 0xF4),    // Mocha Text
                TextSecondary = Color.FromRgb(0x6C, 0x70, 0x86),  // Mocha Subtext0
                AccentColor = Color.FromRgb(0x89, 0xB4, 0xFA),    // Mocha Sapphire
                SuccessColor = Color.FromRgb(0xA6, 0xE3, 0xA1),   // Mocha Green
                DangerColor = Color.FromRgb(0xF3, 0x8B, 0xA8)     // Mocha Red
            },
            ["Cyberpunk"] = new ThemePalette
            {
                Name = "Cyberpunk",
                WindowBg = Color.FromRgb(0x09, 0x00, 0x14),       // Midnight Neon
                SidebarBg = Color.FromRgb(0x05, 0x00, 0x0C),      // Deep synth
                CardBg = Color.FromRgb(0x16, 0x02, 0x26),         // Cyber card
                BorderColor = Color.FromRgb(0x5B, 0x0F, 0x85),    // Neon violet border
                TextPrimary = Color.FromRgb(0x00, 0xF5, 0xD4),    // Electric Cyan
                TextSecondary = Color.FromRgb(0xB5, 0x17, 0x9E),  // Magenta
                AccentColor = Color.FromRgb(0xFF, 0x00, 0x7F),    // Hot Pink
                SuccessColor = Color.FromRgb(0x00, 0xF5, 0xD4),   // Cyan
                DangerColor = Color.FromRgb(0xFF, 0x00, 0x55)     // Red Pink
            },
            ["Emerald"] = new ThemePalette
            {
                Name = "Emerald",
                WindowBg = Color.FromRgb(0x06, 0x10, 0x0A),       // Deep forest shadow
                SidebarBg = Color.FromRgb(0x03, 0x08, 0x05),      // Stealth black-green
                CardBg = Color.FromRgb(0x0D, 0x1C, 0x13),         // Dark emerald card
                BorderColor = Color.FromRgb(0x1A, 0x3A, 0x28),    // Jade border
                TextPrimary = Color.FromRgb(0xEC, 0xFD, 0xF5),    // Mint white
                TextSecondary = Color.FromRgb(0x65, 0x9C, 0x80),  // Sage
                AccentColor = Color.FromRgb(0x10, 0xB9, 0x81),    // Vivid Emerald Green
                SuccessColor = Color.FromRgb(0x34, 0xD3, 0x99),   // Bright Mint
                DangerColor = Color.FromRgb(0xF8, 0x71, 0x71)     // Coral
            },
            ["Crimson"] = new ThemePalette
            {
                Name = "Crimson",
                WindowBg = Color.FromRgb(0x12, 0x07, 0x0A),       // Vampire dark
                SidebarBg = Color.FromRgb(0x0A, 0x03, 0x05),      // Abyssal burgundy
                CardBg = Color.FromRgb(0x1D, 0x0B, 0x12),         // Dark ruby card
                BorderColor = Color.FromRgb(0x3F, 0x14, 0x22),    // Bloodline border
                TextPrimary = Color.FromRgb(0xFF, 0xF1, 0xF2),    // Pale rose
                TextSecondary = Color.FromRgb(0x9E, 0x67, 0x76),  // Muted mauve
                AccentColor = Color.FromRgb(0xE1, 0x1D, 0x48),    // Vivid Crimson Rose
                SuccessColor = Color.FromRgb(0x10, 0xB9, 0x81),   // Jade green
                DangerColor = Color.FromRgb(0xFF, 0x00, 0x33)     // Laser red
            },
            ["Nordic"] = new ThemePalette
            {
                Name = "Nordic",
                WindowBg = Color.FromRgb(0x0E, 0x14, 0x1E),       // Arctic Deep Blue
                SidebarBg = Color.FromRgb(0x08, 0x0C, 0x13),      // Night fjord
                CardBg = Color.FromRgb(0x16, 0x20, 0x2E),         // Glacier navy card
                BorderColor = Color.FromRgb(0x2A, 0x3B, 0x54),    // Frost border
                TextPrimary = Color.FromRgb(0xEE, 0xF2, 0xF6),    // Polar white
                TextSecondary = Color.FromRgb(0x78, 0x8E, 0xA8),  // Slate
                AccentColor = Color.FromRgb(0x60, 0xA5, 0xFA),    // Glacial Ice Blue
                SuccessColor = Color.FromRgb(0x34, 0xD3, 0x99),   // Aurora
                DangerColor = Color.FromRgb(0xF8, 0x71, 0x71)     // Frostbite
            }
        };

        public static void ApplyTheme(Window window, string themeName)
        {
            if (!Themes.TryGetValue(themeName, out var theme))
            {
                theme = Themes["Obsidian"];
            }

            var winBgBrush = new SolidColorBrush(theme.WindowBg);
            var sideBgBrush = new SolidColorBrush(theme.SidebarBg);
            var cardBgBrush = new SolidColorBrush(theme.CardBg);
            var borderBrush = new SolidColorBrush(theme.BorderColor);
            var textPrimaryBrush = new SolidColorBrush(theme.TextPrimary);
            var textSecondaryBrush = new SolidColorBrush(theme.TextSecondary);
            var accentBrush = new SolidColorBrush(theme.AccentColor);
            var successBrush = new SolidColorBrush(theme.SuccessColor);
            var dangerBrush = new SolidColorBrush(theme.DangerColor);

            // 1. Mutate Window.Resources directly so all DynamicResource lookups in MainWindow immediately refresh!
            window.Resources["ColorWindowBg"] = winBgBrush;
            window.Resources["ColorSidebarBg"] = sideBgBrush;
            window.Resources["ColorCardBg"] = cardBgBrush;
            window.Resources["ColorBorder"] = borderBrush;
            window.Resources["ColorTextPrimary"] = textPrimaryBrush;
            window.Resources["ColorTextSecondary"] = textSecondaryBrush;
            window.Resources["ColorAccent"] = accentBrush;
            window.Resources["ColorSuccess"] = successBrush;
            window.Resources["ColorDanger"] = dangerBrush;

            // 2. Also update Application.Current.Resources
            if (Application.Current != null)
            {
                var appRes = Application.Current.Resources;
                appRes["ColorWindowBg"] = winBgBrush;
                appRes["ColorSidebarBg"] = sideBgBrush;
                appRes["ColorCardBg"] = cardBgBrush;
                appRes["ColorBorder"] = borderBrush;
                appRes["ColorTextPrimary"] = textPrimaryBrush;
                appRes["ColorTextSecondary"] = textSecondaryBrush;
                appRes["ColorAccent"] = accentBrush;
                appRes["ColorSuccess"] = successBrush;
                appRes["ColorDanger"] = dangerBrush;
            }

            // 3. Ensure window opacity is solid 1.0 & background matches
            window.Opacity = 1.0;
            window.Background = winBgBrush;
        }
    }
}
