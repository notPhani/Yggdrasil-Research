"""Yggdrasil continuous forensics daemon.

Runs the 15-minute clock loop:
1. Waits for window boundaries
2. Triggers GDELT / live batch ingestion
3. Steps Engines 2a & 2b online
4. Evaluates market trigger conditions
5. Emits snapshots and forensic cases when cutoffs fire
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ygg.determinism import WindowClock, parse_utc

logger = logging.getLogger("ygg.daemon")


@dataclass
class DaemonStatus:
    running: bool
    current_window: int
    last_processed_window: int
    cases_fired: int


class ForensicsDaemon:
    def __init__(self, data_dir: Path, clock: WindowClock):
        self.data_dir = Path(data_dir)
        self.clock = clock
        self.last_window = -1
        self.cases_fired = 0
        self.running = False

    def step_window(self, window_idx: int) -> dict:
        """Execute one atomic step for window_idx."""
        # Simulated step representing ingest -> replay -> trigger check
        self.last_window = window_idx
        return {"status": "ok", "window": window_idx}

    def run_ticks(self, max_ticks: int = 1) -> DaemonStatus:
        """Run up to max_ticks iterations for testing or service loops."""
        self.running = True
        ticks = 0
        while self.running and ticks < max_ticks:
            now = datetime.now(timezone.utc)
            curr_w = self.clock.window_of(now)
            if curr_w > self.last_window:
                self.step_window(curr_w)
            ticks += 1
        self.running = False
        return DaemonStatus(self.running, self.clock.window_of(datetime.now(timezone.utc)), self.last_window, self.cases_fired)
