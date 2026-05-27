"""Core rhythm primitives — beats, tempos, time signatures."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class NoteValue(Enum):
    """Common note durations relative to a whole note."""
    WHOLE = 1.0
    HALF = 0.5
    QUARTER = 0.25
    EIGHTH = 0.125
    SIXTEENTH = 0.0625
    DOTTED_HALF = 0.75
    DOTTED_QUARTER = 0.375
    TRIPLET_QUARTER = 1.0 / 3.0


@dataclass(frozen=True)
class Beat:
    """A single beat with a position in time and an optional velocity."""
    time: float          # absolute time in seconds
    velocity: float = 1.0  # 0.0 – 1.0 intensity
    duration: float = 0.0  # seconds (0 = impulse)

    @property
    def is_accent(self) -> bool:
        return self.velocity >= 0.8

    @property
    def is_rest(self) -> bool:
        return self.velocity == 0.0


@dataclass(frozen=True)
class TimeSignature:
    """Musical time signature (beats per bar, note value per beat)."""
    beats_per_bar: int = 4
    beat_unit: int = 4  # 4 = quarter note

    @property
    def is_compound(self) -> bool:
        return self.beats_per_bar % 3 == 0 and self.beats_per_bar > 3

    @property
    def is_simple(self) -> bool:
        return not self.is_compound

    def bar_duration(self, bpm: float) -> float:
        """Duration of one bar in seconds at the given BPM."""
        beats_per_second = bpm / 60.0
        return self.beats_per_bar / beats_per_second


@dataclass
class Rhythm:
    """A rhythmic sequence with configurable tempo and time signature."""

    beats: list[Beat] = field(default_factory=list)
    bpm: float = 120.0
    time_signature: TimeSignature = field(default_factory=TimeSignature)

    # ── constructors ───────────────────────────────────────────────

    @classmethod
    def from_intervals(
        cls,
        intervals: Sequence[float],
        bpm: float = 120.0,
        time_signature: TimeSignature | None = None,
        velocity: float = 1.0,
    ) -> Rhythm:
        """Create a rhythm from a list of inter-onset intervals (seconds)."""
        ts = time_signature or TimeSignature()
        beats: list[Beat] = []
        t = 0.0
        for gap in intervals:
            beats.append(Beat(time=t, velocity=velocity))
            t += gap
        return cls(beats=beats, bpm=bpm, time_signature=ts)

    @classmethod
    def from_grid(
        cls,
        hits: Sequence[bool],
        subdivision: float = 0.25,
        bpm: float = 120.0,
        time_signature: TimeSignature | None = None,
    ) -> Rhythm:
        """Create a rhythm from a boolean step-sequencer grid.

        *subdivision* is the duration of each step in seconds.
        """
        ts = time_signature or TimeSignature()
        beats: list[Beat] = []
        t = 0.0
        for hit in hits:
            if hit:
                beats.append(Beat(time=t))
            t += subdivision
        return cls(beats=beats, bpm=bpm, time_signature=ts)

    @classmethod
    def steady(
        cls,
        n_beats: int = 8,
        bpm: float = 120.0,
        time_signature: TimeSignature | None = None,
        velocity: float = 1.0,
    ) -> Rhythm:
        """Generate a steady pulse at the given BPM."""
        ts = time_signature or TimeSignature()
        interval = 60.0 / bpm
        beats = [Beat(time=i * interval, velocity=velocity) for i in range(n_beats)]
        return cls(beats=beats, bpm=bpm, time_signature=ts)

    # ── analysis ───────────────────────────────────────────────────

    def intervals(self) -> list[float]:
        """Inter-onset intervals between consecutive beats."""
        out: list[float] = []
        for i in range(1, len(self.beats)):
            out.append(self.beats[i].time - self.beats[i - 1].time)
        return out

    def duration(self) -> float:
        """Total span from first beat to last beat (0 if <2 beats)."""
        if len(self.beats) < 2:
            return 0.0
        return self.beats[-1].time - self.beats[0].time

    def density(self) -> float:
        """Beats per second over the rhythm's span."""
        d = self.duration()
        return len(self.beats) / d if d > 0 else 0.0

    def accent_positions(self) -> list[int]:
        """Indices of accented beats (velocity >= 0.8)."""
        return [i for i, b in enumerate(self.beats) if b.is_accent]

    def bar_count(self) -> int:
        """How many complete bars fit the rhythm at the current BPM/sig."""
        bar_dur = self.time_signature.bar_duration(self.bpm)
        if bar_dur == 0:
            return 0
        return int(self.duration() / bar_dur)

    def quantize(self, grid: float = 0.25) -> Rhythm:
        """Snap beat times to the nearest grid subdivision (seconds)."""
        snapped = [
            Beat(time=round(b.time / grid) * grid, velocity=b.velocity, duration=b.duration)
            for b in self.beats
        ]
        return Rhythm(beats=snapped, bpm=self.bpm, time_signature=self.time_signature)

    def stretch(self, factor: float) -> Rhythm:
        """Time-stretch the rhythm by *factor* (1.0 = unchanged)."""
        stretched = [
            Beat(time=b.time * factor, velocity=b.velocity, duration=b.duration * factor)
            for b in self.beats
        ]
        return Rhythm(
            beats=stretched,
            bpm=self.bpm / factor,
            time_signature=self.time_signature,
        )

    def __len__(self) -> int:
        return len(self.beats)

    def __repr__(self) -> str:
        return (
            f"Rhythm(beats={len(self.beats)}, bpm={self.bpm:.1f}, "
            f"sig={self.time_signature.beats_per_bar}/{self.time_signature.beat_unit})"
        )
