"""Cadence analysis — detect periodic behaviour in event streams."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class CadenceResult:
    """Summary of cadence detected in an event stream."""
    period: float | None          # dominant period in seconds (None if no cadence)
    confidence: float             # 0–1 how strong the periodicity is
    regularity: float             # 0–1 coefficient of variation inverted
    burst_count: int              # number of detected bursts/clusters
    mean_interval: float          # average inter-event interval
    std_interval: float           # std dev of inter-event intervals
    annotations: dict = field(default_factory=dict)


def _autocorrelation(series: Sequence[float], lag: int) -> float:
    """Normalised autocorrelation at a given lag."""
    n = len(series)
    if n < lag + 1:
        return 0.0
    mean = statistics.mean(series)
    denom = sum((x - mean) ** 2 for x in series)
    if denom == 0:
        return 0.0
    numer = sum((series[i] - mean) * (series[i + lag] - mean) for i in range(n - lag))
    return numer / denom


class CadenceAnalyzer:
    """Analyse timestamped event streams for rhythmic cadence."""

    def __init__(
        self,
        min_events: int = 4,
        max_period_ratio: float = 0.5,
        burst_gap: float = 5.0,
    ) -> None:
        self.min_events = min_events
        self.max_period_ratio = max_period_ratio
        self.burst_gap = burst_gap

    # ── public API ─────────────────────────────────────────────────

    def analyse(self, timestamps: Sequence[float]) -> CadenceResult:
        """Analyse a monotonically-sorted list of event timestamps."""
        if len(timestamps) < self.min_events:
            return CadenceResult(
                period=None, confidence=0.0, regularity=0.0,
                burst_count=0, mean_interval=0.0, std_interval=0.0,
            )

        intervals = self._intervals(timestamps)
        mean_iv = statistics.mean(intervals)
        std_iv = statistics.stdev(intervals) if len(intervals) > 1 else 0.0

        # Regularity from coefficient of variation
        cv = std_iv / mean_iv if mean_iv > 0 else float("inf")
        regularity = max(0.0, 1.0 - cv)

        # Detect dominant period via autocorrelation
        period, confidence = self._detect_period(intervals)

        # Burst detection
        burst_count = self._count_bursts(timestamps)

        return CadenceResult(
            period=period,
            confidence=confidence,
            regularity=regularity,
            burst_count=burst_count,
            mean_interval=mean_iv,
            std_interval=std_iv,
        )

    def detect_phase(self, timestamps: Sequence[float]) -> float | None:
        """Estimate the phase offset of the dominant cadence.

        Returns the offset in seconds from the first timestamp, or None
        if no clear cadence is detected.
        """
        if len(timestamps) < self.min_events:
            return None
        result = self.analyse(timestamps)
        if result.period is None or result.confidence < 0.3:
            return None
        # Phase = first timestamp mod period
        return timestamps[0] % result.period

    # ── internals ──────────────────────────────────────────────────

    @staticmethod
    def _intervals(ts: Sequence[float]) -> list[float]:
        return [ts[i] - ts[i - 1] for i in range(1, len(ts))]

    def _detect_period(self, intervals: list[float]) -> tuple[float | None, float]:
        """Find the dominant period using autocorrelation peaks."""
        n = len(intervals)
        if n < 3:
            return None, 0.0

        max_lag = int(n * self.max_period_ratio)
        if max_lag < 2:
            max_lag = 2

        best_lag = 1
        best_corr = -1.0
        for lag in range(1, max_lag + 1):
            corr = _autocorrelation(intervals, lag)
            if corr > best_corr:
                best_corr = corr
                best_lag = lag

        if best_corr < 0.15:
            return None, 0.0

        period = statistics.mean(intervals[:best_lag]) if best_lag <= len(intervals) else None
        confidence = max(0.0, min(1.0, best_corr))
        return period, confidence

    def _count_bursts(self, timestamps: Sequence[float]) -> int:
        if len(timestamps) < 2:
            return len(timestamps)
        bursts = 1
        for i in range(1, len(timestamps)):
            if timestamps[i] - timestamps[i - 1] > self.burst_gap:
                bursts += 1
        return bursts
