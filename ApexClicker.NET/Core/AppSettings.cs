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

        // Visual Bot Persistent Config
        public double VisualConfidenceThreshold { get; set; } = 0.60;
        public int VisualClickAction { get; set; } = 1; // 0=Single, 1=Double, 2=Right
        public bool VisualSmoothMovement { get; set; } = true;
        public int VisualTravelSpeed { get; set; } = 1; // 0=Fast, 1=Smooth, 2=Gentle
        public double VisualCooldownSec { get; set; } = 0.5;
        public double VisualScanIntervalSec { get; set; } = 0.10;
        public int VisualFlowMode { get; set; } = 0; // 0=AnyMatch, 1=Ordered
        public int VisualNotFoundMode { get; set; } = 0; // 0=WaitThenProceed, 1=SkipToNext
        public double VisualStepTimeoutSec { get; set; } = 5.0;
        public bool VisualLoopQueue { get; set; } = true;
        public bool VisualUseRegion { get; set; } = false;
        public int VisualRegionX { get; set; } = 100;
        public int VisualRegionY { get; set; } = 100;
        public int VisualRegionW { get; set; } = 400;
        public int VisualRegionH { get; set; } = 300;
        public int VisualSelectionStrategy { get; set; } = 0; // 0=HighestConfidence, 1=ClosestToCursor
        public string LastVisualPreset { get; set; } = "Default";

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
