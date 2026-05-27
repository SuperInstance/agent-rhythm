"""Tempo tracking — BPM detection, changes, acceleration/deceleration."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class TempoChange:
    """A detected change in tempo."""
    time: float            # when the change occurred (seconds)
    bpm_before: float      # tempo before the change
    bpm_after: float       # tempo after the change
    rate: float            # bpm_after / bpm_before (>1 = accel, <1 = decel)

    @property
    def is_accelerando(self) -> bool:
        return self.rate > 1.0

    @property
    def is_ritardando(self) -> bool:
        return self.rate < 1.0

    @property
    def delta_bpm(self) -> float:
        return self.bpm_after - self.bpm_before


@dataclass
class TempoTracker:
    """Track tempo over a sequence of beat timestamps.

    Parameters
    ----------
    window : int
        Rolling window size for local BPM estimation.
    change_threshold : float
        Minimum ratio change to count as a tempo change event.
    """

    window: int = 4
    change_threshold: float = 0.10

    # ── public API ─────────────────────────────────────────────────

    def analyse(self, beat_times: Sequence[float]) -> list[TempoChange]:
        """Detect tempo changes across a sequence of beat timestamps."""
        if len(beat_times) < self.window + 1:
            return []

        local_bpms = self._rolling_bpm(beat_times)
        changes: list[TempoChange] = []

        for i in range(1, len(local_bpms)):
            t = beat_times[min(i + self.window // 2, len(beat_times) - 1)]
            bpm_before = local_bpms[i - 1]
            bpm_after = local_bpms[i]
            if bpm_before == 0:
                continue
            ratio = bpm_after / bpm_before
            if abs(ratio - 1.0) >= self.change_threshold:
                changes.append(TempoChange(
                    time=t,
                    bpm_before=bpm_before,
                    bpm_after=bpm_after,
                    rate=ratio,
                ))

        return changes

    def global_bpm(self, beat_times: Sequence[float]) -> float:
        """Overall BPM estimate from the full sequence."""
        if len(beat_times) < 2:
            return 0.0
        intervals = [beat_times[i] - beat_times[i - 1] for i in range(1, len(beat_times))]
        if not intervals:
            return 0.0
        # Use median for robustness against outliers
        med = statistics.median(intervals)
        return 60.0 / med if med > 0 else 0.0

    def instant_bpm(self, beat_times: Sequence[float]) -> list[float]:
        """Instantaneous BPM at each beat (after the first)."""
        out: list[float] = []
        for i in range(1, len(beat_times)):
            iv = beat_times[i] - beat_times[i - 1]
            out.append(60.0 / iv if iv > 0 else 0.0)
        return out

    def detect_acceleration(
        self, beat_times: Sequence[float]
    ) -> tuple[list[TempoChange], list[TempoChange]]:
        """Split tempo changes into accelerandos and ritardandos."""
        changes = self.analyse(beat_times)
        accel = [c for c in changes if c.is_accelerando]
        decel = [c for c in changes if c.is_ritardando]
        return accel, decel

    def bpm_curve(self, beat_times: Sequence[float]) -> list[tuple[float, float]]:
        """Return (time, bpm) pairs for plotting tempo over time."""
        local = self._rolling_bpm(beat_times)
        # Map each windowed BPM to the centre time of its window
        half = self.window // 2
        pairs: list[tuple[float, float]] = []
        for i, bpm in enumerate(local):
            idx = min(i + half, len(beat_times) - 1)
            pairs.append((beat_times[idx], bpm))
        return pairs

    # ── internals ──────────────────────────────────────────────────

    def _rolling_bpm(self, beat_times: Sequence[float]) -> list[float]:
        """Compute rolling-window BPM estimates."""
        bpms: list[float] = []
        n = len(beat_times)
        for start in range(n - self.window + 1):
            segment = beat_times[start: start + self.window]
            total = segment[-1] - segment[0]
            if total <= 0:
                bpms.append(0.0)
                continue
            bpm = (self.window - 1) / total * 60.0
            bpms.append(bpm)
        return bpms
