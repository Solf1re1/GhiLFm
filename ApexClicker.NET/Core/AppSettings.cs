using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace ApexClicker.Core
{
    public class AppSettings
    {
        // General & Window
        public string Theme { get; set; } = "Obsidian";
        public double WindowOpacity { get; set; } = 1.0;
        public string LastActiveTab { get; set; } = "burst";
        public double? WindowLeft { get; set; } = null;
        public double? WindowTop { get; set; } = null;
        public double? WindowWidth { get; set; } = null;
        public double? WindowHeight { get; set; } = null;
        public double? OverlayX { get; set; } = null;
        public double? OverlayY { get; set; } = null;

        // Module Toggles
        public bool ShowBurst { get; set; } = true;
        public bool ShowSequence { get; set; } = true;
        public bool ShowPixelTrigger { get; set; } = true;
        public bool ShowVisualBot { get; set; } = true;
        public bool ShowKeySpammer { get; set; } = true;
        public bool ShowMacroStudio { get; set; } = true;

        // Burst Clicker Settings
        public int BurstCps { get; set; } = 100;
        public int BurstMouseButton { get; set; } = 0; // 0=Left, 1=Right, 2=Middle
        public int BurstClickMode { get; set; } = 0; // 0=Single, 1=Double
        public bool BurstFollowCursor { get; set; } = true;
        public int BurstFixedX { get; set; } = 500;
        public int BurstFixedY { get; set; } = 500;

        // Key Spammer Settings
        public string KeySpamKeys { get; set; } = "1, 2, 3, E, Space";
        public int KeySpamIntervalMs { get; set; } = 100;

        // Pixel Trigger Settings
        public int PixelX { get; set; } = 100;
        public int PixelY { get; set; } = 100;
        public string PixelColorHex { get; set; } = "#00FF00";

        // Sequence / Multi-Point Settings
        public string SequencePointsJson { get; set; } = "";
        public int SequenceRepeatCount { get; set; } = 0;

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
        public int VisualClickOffsetX { get; set; } = 0;
        public int VisualClickOffsetY { get; set; } = 0;
        public string LastVisualPreset { get; set; } = "Default";
        public string VisualTargetsJson { get; set; } = "";

        public static string AppDataDirectory
        {
            get
            {
                string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ApexClicker");
                Directory.CreateDirectory(dir);
                return dir;
            }
        }

        public static string SettingsPath => Path.Combine(AppDataDirectory, "settings.json");

        public static void MigrateLegacySettingsIfFound()
        {
            try
            {
                string localBase = AppDomain.CurrentDomain.BaseDirectory;
                string appData = AppDataDirectory;

                // 1. Migrate settings.json
                string localSettings = Path.Combine(localBase, "settings.json");
                string appDataSettings = Path.Combine(appData, "settings.json");
                if (File.Exists(localSettings) && !File.Exists(appDataSettings))
                {
                    File.Copy(localSettings, appDataSettings, true);
                }

                // 2. Migrate profiles/visual_bot
                string localProfiles = Path.Combine(localBase, "profiles", "visual_bot");
                string appDataProfiles = Path.Combine(appData, "profiles", "visual_bot");
                if (Directory.Exists(localProfiles))
                {
                    Directory.CreateDirectory(appDataProfiles);
                    foreach (var file in Directory.GetFiles(localProfiles, "*.json"))
                    {
                        string dest = Path.Combine(appDataProfiles, Path.GetFileName(file));
                        if (!File.Exists(dest))
                        {
                            File.Copy(file, dest, true);
                        }
                    }
                }

                // 3. Migrate templates
                string localTemplates = Path.Combine(localBase, "templates");
                string appDataTemplates = Path.Combine(appData, "templates");
                if (Directory.Exists(localTemplates))
                {
                    Directory.CreateDirectory(appDataTemplates);
                    foreach (var file in Directory.GetFiles(localTemplates, "*.png"))
                    {
                        string dest = Path.Combine(appDataTemplates, Path.GetFileName(file));
                        if (!File.Exists(dest))
                        {
                            File.Copy(file, dest, true);
                        }
                    }
                }
            }
            catch { }
        }

        public static AppSettings Load()
        {
            MigrateLegacySettingsIfFound();

            try
            {
                string path = SettingsPath;
                if (!File.Exists(path))
                {
                    // Fallback to local settings.json if present
                    string localPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "settings.json");
                    if (File.Exists(localPath)) path = localPath;
                }

                if (File.Exists(path))
                {
                    string json = File.ReadAllText(path);
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
                
                // Save primary persistent copy in %APPDATA%\ApexClicker
                File.WriteAllText(SettingsPath, json);

                // Mirror copy in local directory for portable setups
                try
                {
                    string localPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "settings.json");
                    File.WriteAllText(localPath, json);
                }
                catch { }
            }
            catch { }
        }
    }
}
