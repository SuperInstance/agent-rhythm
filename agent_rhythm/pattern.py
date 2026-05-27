"""Pattern matching — recognise rhythmic patterns, polyrhythms, syncopation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from .rhythm import Beat, Rhythm, TimeSignature


@dataclass(frozen=True)
class Pattern:
    """A recognised rhythmic pattern."""
    name: str
    description: str
    grid: list[bool]       # step-sequencer representation
    subdivision: float      # seconds per step

    @property
    def step_count(self) -> int:
        return len(self.grid)

    @property
    def hit_count(self) -> int:
        return sum(self.grid)

    def to_rhythm(self, bpm: float = 120.0) -> Rhythm:
        return Rhythm.from_grid(self.grid, subdivision=self.subdivision, bpm=bpm)

    @property
    def density(self) -> float:
        return self.hit_count / self.step_count if self.step_count else 0.0


# ── built-in pattern library ───────────────────────────────────────

BUILTIN_PATTERNS: dict[str, Pattern] = {
    "four-on-floor": Pattern(
        name="four-on-floor",
        description="Classic kick drum pattern — every quarter note",
        grid=[True, False, False, False] * 4,
        subdivision=0.25,
    ),
    "bo-diddley": Pattern(
        name="bo-diddley",
        description="3-3-4-2 or hambone rhythm",
        grid=[True, True, False, True, True, True, False, True, True, False, True, False],
        subdivision=1.0 / 6.0,
    ),
    "tresillo": Pattern(
        name="tresillo",
        description="Cuban 3+3+2 pattern over 8 steps",
        grid=[True, False, False, True, False, False, True, False],
        subdivision=0.25,
    ),
    "son-clave": Pattern(
        name="son-clave",
        description="2-3 son clave",
        grid=[True, False, True, False, False, True, True, False, True, False, False, False, True, False, False, False],
        subdivision=0.125,
    ),
    "rumba-clave": Pattern(
        name="rumba-clave",
        description="2-3 rumba clave",
        grid=[True, False, True, False, False, True, False, True, False, False, True, False, False, True, False, False],
        subdivision=0.125,
    ),
    "shuffle": Pattern(
        name="shuffle",
        description="Swung 8th-note feel with long-short pairs",
        grid=[True, False, True, False, True, False, True, False, True, False, True, False],
        subdivision=1.0 / 6.0,
    ),
}


def _normalize_grid(grid: list[bool]) -> list[bool]:
    """Trim leading/trailing rests and ensure non-empty."""
    first = 0
    while first < len(grid) and not grid[first]:
        first += 1
    last = len(grid)
    while last > first and not grid[last - 1]:
        last -= 1
    return grid[first:last] if first < last else [True]


def _circular_correlation(a: list[bool], b: list[bool]) -> float:
    """Binary circular cross-correlation — 1.0 = perfect match."""
    la, lb = len(a), len(b)
    length = max(la, lb)
    # Pad both to same length
    ap = list(a) + [False] * (length - la)
    bp = list(b) + [False] * (length - lb)
    total_on = sum(ap) + sum(bp)
    if total_on == 0:
        return 0.0

    best = 0
    for shift in range(length):
        matches = sum(1 for i in range(length) if ap[i] == bp[(i + shift) % length] and ap[i])
        if matches > best:
            best = matches
    expected = min(sum(ap), sum(bp))
    return best / expected if expected > 0 else 0.0


@dataclass
class PatternMatcher:
    """Match rhythms against known patterns and detect polyrhythms/syncopation."""

    patterns: dict[str, Pattern] = field(default_factory=lambda: dict(BUILTIN_PATTERNS))
    match_threshold: float = 0.7

    # ── public API ─────────────────────────────────────────────────

    def match(self, rhythm: Rhythm) -> list[tuple[Pattern, float]]:
        """Find the best-matching known patterns for *rhythm*.

        Returns a list of (Pattern, score) tuples sorted by score descending.
        """
        if not rhythm.beats:
            return []

        interval = 60.0 / rhythm.bpm if rhythm.bpm > 0 else 0.5
        sub = interval / 4  # 16th-note subdivision
        grid = self._rhythm_to_grid(rhythm, sub)
        results: list[tuple[Pattern, float]] = []

        for pattern in self.patterns.values():
            # Resample both grids to the same length via proportional mapping
            p_grid = self._resample_grid(pattern.grid, len(grid))
            score = _circular_correlation(grid, p_grid)
            if score >= self.match_threshold:
                results.append((pattern, score))

        results.sort(key=lambda t: t[1], reverse=True)
        return results

    def best_match(self, rhythm: Rhythm) -> Pattern | None:
        """Return the single best-matching pattern, or None."""
        matches = self.match(rhythm)
        return matches[0][0] if matches else None

    def detect_syncopation(self, rhythm: Rhythm) -> float:
        """Score how syncopated a rhythm is (0 = none, 1 = maximum).

        Syncopation is measured as the proportion of beats falling on
        off-beat (weak) positions within the bar.
        """
        if len(rhythm.beats) < 2 or rhythm.bpm <= 0:
            return 0.0

        beat_dur = 60.0 / rhythm.bpm
        bar_dur = rhythm.time_signature.bar_duration(rhythm.bpm)
        if bar_dur <= 0:
            return 0.0

        syncopated = 0
        total = 0
        for b in rhythm.beats:
            pos_in_bar = b.time % bar_dur
            # Distance to nearest strong beat
            nearest_downbeat = round(pos_in_bar / beat_dur) * beat_dur
            offset = abs(pos_in_bar - nearest_downbeat)
            if offset > beat_dur * 0.1:  # more than 10% off = syncopated
                syncopated += 1
            total += 1

        return syncopated / total if total > 0 else 0.0

    def detect_polyrhythm(self, rhythm: Rhythm) -> list[tuple[int, int, float]]:
        """Detect polyrhythmic structure: list of (voice_a, voice_b, strength).

        Returns tuples of two integer layer counts and a confidence score.
        """
        if len(rhythm.beats) < 4:
            return []

        intervals = rhythm.intervals()
        if not intervals:
            return []

        # Cluster intervals by similarity
        sorted_iv = sorted(intervals)
        clusters: list[list[float]] = []
        eps = min(sorted_iv) * 0.15

        current_cluster = [sorted_iv[0]]
        for iv in sorted_iv[1:]:
            if abs(iv - current_cluster[0]) <= eps:
                current_cluster.append(iv)
            else:
                clusters.append(current_cluster)
                current_cluster = [iv]
        clusters.append(current_cluster)

        # If we see two dominant interval groups, it's a polyrhythm
        if len(clusters) < 2:
            return []

        clusters.sort(key=len, reverse=True)
        results: list[tuple[int, int, float]] = []
        for i in range(min(3, len(clusters) - 1)):
            a, b = len(clusters[0]), len(clusters[i + 1])
            total = a + b
            strength = min(a, b) / math.gcd(a, b) / 10.0  # heuristic normalise
            strength = min(1.0, strength)
            ratio = (max(a, b), min(a, b))
            results.append((ratio[0], ratio[1], strength))

        return results

    def register_pattern(self, pattern: Pattern) -> None:
        self.patterns[pattern.name] = pattern

    # ── internals ──────────────────────────────────────────────────

    @staticmethod
    def _rhythm_to_grid(rhythm: Rhythm, subdivision: float) -> list[bool]:
        """Convert a rhythm to a boolean step grid."""
        if not rhythm.beats or subdivision <= 0:
            return []
        start = rhythm.beats[0].time
        end = rhythm.beats[-1].time
        span = end - start
        if span <= 0:
            return [True]
        steps = max(1, round(span / subdivision) + 1)
        grid = [False] * steps
        for b in rhythm.beats:
            idx = round((b.time - start) / subdivision)
            if 0 <= idx < steps:
                grid[idx] = True
        return _normalize_grid(grid)

    @staticmethod
    def _resample_grid(grid: list[bool], target_len: int) -> list[bool]:
        """Proportionally stretch/compress a grid to *target_len* steps."""
        if not grid or target_len <= 0:
            return [False] * max(1, target_len)
        out: list[bool] = []
        for i in range(target_len):
            src = int(i / target_len * len(grid))
            out.append(grid[min(src, len(grid) - 1)])
        return out
