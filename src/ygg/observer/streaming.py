"""Streaming market observer: 1-minute bar accumulator and intraday anomaly detector."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np


@dataclass(frozen=True, slots=True)
class StreamingBar:
    symbol: str
    timestamp: datetime  # UTC aware
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class AnomalyAlert:
    symbol: str
    timestamp: datetime
    return_z: float
    vol_ratio: float
    is_anomaly: bool


class StreamingAnomalyDetector:
    def __init__(self, z_thresh: float = 4.0, vol_thresh: float = 3.5, window_bars: int = 60):
        self.z_thresh = z_thresh
        self.vol_thresh = vol_thresh
        self.window_bars = window_bars
        self.history: dict[str, list[StreamingBar]] = defaultdict(list)

    def push_bar(self, bar: StreamingBar) -> AnomalyAlert:
        """Push a 1-minute bar and return anomaly evaluation."""
        bars = self.history[bar.symbol]
        bars.append(bar)
        if len(bars) > self.window_bars:
            bars.pop(0)

        if len(bars) < 15:
            return AnomalyAlert(bar.symbol, bar.timestamp, 0.0, 1.0, False)

        closes = np.array([b.close for b in bars])
        volumes = np.array([b.volume for b in bars])

        returns = np.diff(closes) / closes[:-1]
        last_ret = returns[-1]
        ret_mean = np.mean(returns[:-1])
        ret_std = np.std(returns[:-1])
        z = (last_ret - ret_mean) / (ret_std + 1e-8)

        v_mean = np.mean(volumes[:-1])
        v_ratio = bar.volume / (v_mean + 1.0)

        is_anom = bool((abs(z) >= self.z_thresh) and (v_ratio >= self.vol_thresh))
        return AnomalyAlert(bar.symbol, bar.timestamp, float(z), float(v_ratio), is_anom)
