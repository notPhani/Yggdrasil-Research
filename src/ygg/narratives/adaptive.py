"""Adaptive emergence engine: dynamic scaling for event-cluster to narrative transition.

Replaces the static m_emerge integer with a dual-regime gate:
1. Diurnal Rate Scaling: m_rate*(t) = max(m_min, ceil(rho * V_bar_6h))
2. Velocity Surge Gating: mass >= m_min AND (mass / dt_h) >= v_burst
Also caps total alive narratives at max_alive to prevent graph explosion.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass


@dataclass
class AdaptiveConfig:
    m_min: int = 3
    rho: float = 0.004
    v_burst_base: float = 2.5
    horizon_windows: int = 24  # trailing 6 hours
    v_daily_baseline: float = 5000.0
    max_alive: int = 300


class AdaptiveEmergence:
    def __init__(self, cfg: AdaptiveConfig = AdaptiveConfig()):
        self.cfg = cfg
        self.vol_history: deque[int] = deque(maxlen=cfg.horizon_windows)
        self.cluster_first_h: dict[int, float] = {}

    def record_window(self, roots_count: int) -> None:
        """Call once at the end of each window with the number of root documents."""
        self.vol_history.append(roots_count)

    def current_m_rate(self) -> int:
        """Compute the rate-scaled mass threshold for the current time window."""
        if not self.vol_history:
            return self.cfg.m_min
        v_bar = sum(self.vol_history) / float(len(self.vol_history))
        return max(self.cfg.m_min, math.ceil(self.cfg.rho * v_bar))

    def should_emerge(self, cid: int, mass: int, t_h: float, num_alive: int) -> bool:
        """Determines if event cluster cid has earned narrative status."""
        # Safety brake: if alive narratives already at capacity, enforce stricter threshold
        if num_alive >= self.cfg.max_alive:
            return mass >= (self.current_m_rate() * 2)

        if cid not in self.cluster_first_h:
            self.cluster_first_h[cid] = t_h

        # Gate 1: Rate-scaled cumulative mass
        if mass >= self.current_m_rate():
            return True

        # Gate 2: Acute velocity surge (e.g. breaking shock)
        dt_h = max(t_h - self.cluster_first_h[cid], 0.25)
        velocity = mass / dt_h

        v_bar = sum(self.vol_history) / float(len(self.vol_history)) if self.vol_history else self.cfg.v_daily_baseline
        v_thresh = max(self.cfg.v_burst_base, 3.0 * (v_bar / self.cfg.v_daily_baseline))

        return (mass >= self.cfg.m_min and velocity >= v_thresh)
