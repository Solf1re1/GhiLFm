using System;
using System.Diagnostics;
using System.Threading;
using ApexClicker.Native;

namespace ApexClicker.Core
{
    public class Humanizer
    {
        private readonly Random _rand = new();

        public bool EnableHumanMovement { get; set; } = true;
        public bool EnableTimingJitter { get; set; } = true;
        public double TimingJitterRangeMs { get; set; } = 2.0;
        public bool EnableOffsetJitter { get; set; } = true;
        public int OffsetJitterRadius { get; set; } = 3;

        public double GetRandomJitteredInterval(double baseIntervalMs)
        {
            if (!EnableTimingJitter || TimingJitterRangeMs <= 0)
                return Math.Max(0.5, baseIntervalMs);

            // Box-Muller transform for true Gaussian distribution
            double u1 = 1.0 - _rand.NextDouble();
            double u2 = 1.0 - _rand.NextDouble();
            double randStdNormal = Math.Sqrt(-2.0 * Math.Log(u1)) * Math.Sin(2.0 * Math.PI * u2);

            double jitter = randStdNormal * (TimingJitterRangeMs / 2.0);
            return Math.Max(0.5, baseIntervalMs + jitter);
        }

        public (int X, int Y) ApplyOffsetJitter(int x, int y)
        {
            if (!EnableOffsetJitter || OffsetJitterRadius <= 0)
                return (x, y);

            double angle = _rand.NextDouble() * Math.PI * 2.0;
            double radius = Math.Sqrt(_rand.NextDouble()) * OffsetJitterRadius;

            int jx = x + (int)Math.Round(radius * Math.Cos(angle));
            int jy = y + (int)Math.Round(radius * Math.Sin(angle));
            return (jx, jy);
        }

        public void MoveSmoothly(int startX, int startY, int endX, int endY, int durationMs = 120)
        {
            if (!EnableHumanMovement || durationMs <= 5)
            {
                Win32Api.SetCursorPos(endX, endY);
                return;
            }

            // Generate random Bezier control points
            int dx = endX - startX;
            int dy = endY - startY;

            double deviation = Math.Max(20.0, Math.Sqrt(dx * dx + dy * dy) * 0.25);
            int ctrl1X = startX + (int)(dx * 0.3) + _rand.Next((int)-deviation, (int)deviation);
            int ctrl1Y = startY + (int)(dy * 0.3) + _rand.Next((int)-deviation, (int)deviation);
            int ctrl2X = startX + (int)(dx * 0.7) + _rand.Next((int)-deviation, (int)deviation);
            int ctrl2Y = startY + (int)(dy * 0.7) + _rand.Next((int)-deviation, (int)deviation);

            int steps = Math.Max(10, durationMs / 8);
            long frequency = Stopwatch.Frequency;
            double stepDelaySec = (double)durationMs / steps / 1000.0;

            for (int i = 1; i <= steps; i++)
            {
                double t = (double)i / steps;
                // Ease in-out cubic
                double tEased = t < 0.5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2;

                // Cubic Bezier formula
                double u = 1 - tEased;
                double tt = tEased * tEased;
                double uu = u * u;
                double uuu = uu * u;
                double ttt = tt * tEased;

                double px = uuu * startX + 3 * uu * tEased * ctrl1X + 3 * u * tt * ctrl2X + ttt * endX;
                double py = uuu * startY + 3 * uu * tEased * ctrl1Y + 3 * u * tt * ctrl2Y + ttt * endY;

                Win32Api.SetCursorPos((int)Math.Round(px), (int)Math.Round(py));

                // Precise wait
                long start = Stopwatch.GetTimestamp();
                long targetTicks = (long)(stepDelaySec * frequency);
                while (Stopwatch.GetTimestamp() - start < targetTicks)
                {
                    Thread.SpinWait(5);
                }
            }

            Win32Api.SetCursorPos(endX, endY);
        }
    }
}
