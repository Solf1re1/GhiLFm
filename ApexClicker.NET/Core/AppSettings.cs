using System;
using System.IO;
using System.Text.Json;

namespace ApexClicker.Core
{
    public class AppSettings
    {
        public string Theme { get; set; } = "Obsidian";
        public double WindowOpacity { get; set; } = 1.0;

        // Overlay Coordinates
        public double? OverlayX { get; set; } = null;
        public double? OverlayY { get; set; } = null;

        // Module Toggles (Option 1: In-App Feature Selector)
        public bool ShowBurst { get; set; } = true;
        public bool ShowSequence { get; set; } = true;
        public bool ShowPixelTrigger { get; set; } = true;
        public bool ShowVisualBot { get; set; } = true;
        public bool ShowKeySpammer { get; set; } = true;
        public bool ShowMacroStudio { get; set; } = true;
        public bool ShowAutomationStudio { get; set; } = true;

        private static readonly string SettingsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "settings.json");

        public static AppSettings Load()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    string json = File.ReadAllText(SettingsPath);
                    var settings = JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
                    if (string.IsNullOrWhiteSpace(settings.Theme) || settings.Theme.Equals("Transparent", StringComparison.OrdinalIgnoreCase))
                    {
                        settings.Theme = "Obsidian";
                    }
                    return settings;
                }
            }
            catch { }
            return new AppSettings();
        }

        public void Save()
        {
            try
            {
                string json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(SettingsPath, json);
            }
            catch { }
        }
    }
}
