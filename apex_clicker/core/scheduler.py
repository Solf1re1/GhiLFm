"""
Scheduled Timer & Auto-Shutdown Engine.
Monitors session duration, countdown timers, and executes completion triggers
such as alarm beeps, PC sleep, or system shutdown.
"""

import os
import subprocess
import time
import winsound
from typing import Optional, Callable


class SessionScheduler:
    """Tracks duration limits and executes post-completion actions."""

    ACTION_STOP = "STOP"
    ACTION_BEEP = "BEEP"
    ACTION_SLEEP = "SLEEP"
    ACTION_SHUTDOWN = "SHUTDOWN"

    def __init__(self):
        self.enabled = False
        self.duration_seconds = 0.0  # 0 = disabled
        self.action = self.ACTION_STOP
        self.start_time = 0.0
        self.elapsed_before_pause = 0.0

    def start(self):
        """Starts or resumes the scheduler countdown."""
        self.start_time = time.perf_counter()

    def pause(self):
        """Pauses the scheduler timer."""
        if self.start_time > 0:
            self.elapsed_before_pause += time.perf_counter() - self.start_time
            self.start_time = 0.0

    def reset(self):
        """Resets the timer counters."""
        self.start_time = 0.0
        self.elapsed_before_pause = 0.0

    def get_remaining_seconds(self) -> float:
        """Returns remaining seconds until completion. Negative if expired."""
        if not self.enabled or self.duration_seconds <= 0:
            return 0.0

        current_elapsed = self.elapsed_before_pause
        if self.start_time > 0:
            current_elapsed += time.perf_counter() - self.start_time

        return max(0.0, self.duration_seconds - current_elapsed)

    def is_expired(self) -> bool:
        """Returns True if the scheduled duration has elapsed."""
        if not self.enabled or self.duration_seconds <= 0:
            return False
        return self.get_remaining_seconds() <= 0.0

    def format_remaining(self) -> str:
        """Returns HH:MM:SS string."""
        rem = int(self.get_remaining_seconds())
        h = rem // 3600
        m = (rem % 3600) // 60
        s = rem % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def execute_completion_action(self):
        """Executes the chosen post-run action."""
        if self.action == self.ACTION_BEEP:
            try:
                for _ in range(3):
                    winsound.Beep(1000, 150)
                    time.sleep(0.1)
            except Exception:
                pass
        elif self.action == self.ACTION_SLEEP:
            try:
                # Windows Sleep / Suspend
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            except Exception:
                pass
        elif self.action == self.ACTION_SHUTDOWN:
            try:
                # Shutdown in 30 seconds with warning
                subprocess.run(["shutdown.exe", "/s", "/t", "30", "/c", "ApexClicker scheduled shutdown initiated."])
            except Exception:
                pass
