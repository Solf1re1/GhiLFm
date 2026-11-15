using System;
using System.IO;
using System.Reflection;
using System.Windows;
using System.Windows.Threading;
using ApexClicker.Core;

namespace ApexClicker;

public partial class App : Application
{
    public App()
    {
        // 1. Eagerly resolve and load System.Diagnostics.Tracing in memory
        // This permanently fixes WPF ControlsTraceLogger failing to locate the assembly during Windows shutdown/reboot
        AppDomain.CurrentDomain.AssemblyResolve += (sender, args) =>
        {
            if (args.Name.StartsWith("System.Diagnostics.Tracing", StringComparison.OrdinalIgnoreCase))
            {
                return typeof(System.Diagnostics.Tracing.EventSource).Assembly;
            }
            return null;
        };

        try
        {
            _ = typeof(System.Diagnostics.Tracing.EventSource).Assembly;
        }
        catch { }

        AppDomain.CurrentDomain.UnhandledException += (s, e) =>
        {
            try
            {
                string crashPath = Path.Combine(AppSettings.AppDataDirectory, "crash.log");
                File.WriteAllText(crashPath, e.ExceptionObject?.ToString() ?? "Unknown exception");
            }
            catch { }
        };

        DispatcherUnhandledException += (s, e) =>
        {
            try
            {
                string crashPath = Path.Combine(AppSettings.AppDataDirectory, "crash.log");
                File.WriteAllText(crashPath, e.Exception?.ToString() ?? "Unknown exception");
            }
            catch { }

            // Never block Windows OS shutdown, logoff, or reboot with modal error message dialogs
            string exStr = e.Exception?.ToString() ?? "";
            bool isShutdownException = exStr.Contains("ControlsTraceLogger") ||
                                       exStr.Contains("CriticalShutdown") ||
                                       exStr.Contains("WmQueryEndSession") ||
                                       exStr.Contains("WmEndSession");

            if (!isShutdownException)
            {
                MessageBox.Show(e.Exception?.Message ?? "An unexpected error occurred.", "ApexClicker Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }

            e.Handled = true;
        };

        SessionEnding += (s, e) =>
        {
            try
            {
                if (MainWindow is MainWindow mw)
                {
                    mw.Close();
                }
            }
            catch { }
        };
    }
}
