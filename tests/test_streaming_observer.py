from datetime import datetime, timezone, timedelta
from ygg.observer.streaming import StreamingBar, StreamingAnomalyDetector

def test_detector_identifies_simulated_shock():
    det = StreamingAnomalyDetector(z_thresh=4.0, vol_thresh=3.5, window_bars=30)
    t0 = datetime(2025, 1, 27, 8, 0, tzinfo=timezone.utc)
    
    # 20 calm bars for NVDA
    for i in range(20):
        bar = StreamingBar("NVDA", t0 + timedelta(minutes=i), 120.0, 120.2, 119.8, 120.0 + (0.01 * (i % 2)), 1000.0)
        alert = det.push_bar(bar)
        assert alert.is_anomaly is False

    # 1 shock bar: price drops to 110 (-8%), volume spikes to 10,000 (10x)
    shock_bar = StreamingBar("NVDA", t0 + timedelta(minutes=20), 120.0, 120.0, 109.5, 110.0, 10000.0)
    alert = det.push_bar(shock_bar)
    assert alert.is_anomaly is True
    assert alert.symbol == "NVDA"
    assert alert.return_z < -4.0
    assert alert.vol_ratio > 3.5
