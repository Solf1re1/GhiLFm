using System;
using System.IO;
using System.Windows;
using System.Windows.Threading;

namespace ApexClicker;

public partial class App : Application
{
    public App()
    {
        AppDomain.CurrentDomain.UnhandledException += (s, e) =>
        {
            File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log"), e.ExceptionObject.ToString());
        };

        DispatcherUnhandledException += (s, e) =>
        {
            File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log"), e.Exception.ToString());
            MessageBox.Show(e.Exception.ToString(), "ApexClicker Error", MessageBoxButton.OK, MessageBoxImage.Error);
            e.Handled = true;
        };
    }
}
