from datetime import datetime, timezone
from pathlib import Path
from ygg.daemon import ForensicsDaemon
from ygg.determinism import WindowClock

def test_daemon_ticks_cleanly(tmp_path):
    clock = WindowClock(datetime(2025, 1, 27, 0, 0, tzinfo=timezone.utc), delta_s=900)
    daemon = ForensicsDaemon(tmp_path, clock)
    status = daemon.run_ticks(max_ticks=2)
    assert status.running is False
    assert status.last_processed_window >= 0
