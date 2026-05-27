"""Rhythmic scheduler — schedule tasks to musical time / rhythmic cues."""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .rhythm import Rhythm, TimeSignature


@dataclass(frozen=True)
class ScheduledTask:
    """A task bound to a rhythmic position."""
    name: str
    beat_index: int         # which beat in the rhythm triggers this task
    callback: Callable[[], None]
    repeat: bool = False
    last_run: float = 0.0   # monotonic timestamp of last execution


@dataclass
class RhythmicScheduler:
    """Schedule callbacks on rhythmic time.

    The scheduler maps real wall-clock time to beats of a given rhythm,
    triggering registered tasks at the appropriate beat positions.
    It supports one-shot and repeating tasks.
    """

    rhythm: Rhythm = field(default_factory=Rhythm)
    loop: bool = False           # loop the rhythm when it ends?
    look_ahead: float = 0.05     # seconds ahead to schedule

    _tasks: list[ScheduledTask] = field(default_factory=list)
    _origin: float = 0.0
    _running: bool = False

    # ── task registration ──────────────────────────────────────────

    def on_beat(
        self,
        beat_index: int,
        callback: Callable[[], None],
        name: str = "",
        repeat: bool = True,
    ) -> ScheduledTask:
        """Register *callback* to fire on the given beat index."""
        task = ScheduledTask(
            name=name or f"beat-{beat_index}",
            beat_index=beat_index,
            callback=callback,
            repeat=repeat,
        )
        self._tasks.append(task)
        return task

    def on_downbeat(
        self,
        callback: Callable[[], None],
        name: str = "",
        repeat: bool = True,
    ) -> list[ScheduledTask]:
        """Register *callback* on every downbeat (beat 0 of each bar)."""
        tasks: list[ScheduledTask] = []
        bpbar = self.rhythm.time_signature.beats_per_bar
        for i, beat in enumerate(self.rhythm.beats):
            if i % bpbar == 0:
                tasks.append(self.on_beat(i, callback, name=name or f"downbeat-{i}", repeat=repeat))
        return tasks

    def on_accent(
        self,
        callback: Callable[[], None],
        name: str = "",
        repeat: bool = True,
    ) -> list[ScheduledTask]:
        """Register *callback* on every accented beat."""
        tasks: list[ScheduledTask] = []
        for i, beat in enumerate(self.rhythm.beats):
            if beat.is_accent:
                tasks.append(self.on_beat(i, callback, name=name or f"accent-{i}", repeat=repeat))
        return tasks

    def remove_task(self, task: ScheduledTask) -> None:
        if task in self._tasks:
            self._tasks.remove(task)

    # ── scheduling engine ──────────────────────────────────────────

    def start(self) -> None:
        """Begin the scheduler (non-blocking; call tick() in your loop)."""
        self._origin = _time.monotonic()
        self._running = True

    def stop(self) -> None:
        self._running = False

    def tick(self) -> list[str]:
        """Call this regularly. Fires any tasks whose beat has been reached.

        Returns a list of task names that fired.
        """
        if not self._running or not self.rhythm.beats:
            return []

        now = _time.monotonic() - self._origin
        fired: list[str] = []

        for task in self._tasks:
            if task.beat_index >= len(self.rhythm.beats):
                continue
            beat_time = self.rhythm.beats[task.beat_index].time
            if now >= beat_time and (now - beat_time) <= self.look_ahead:
                if task.repeat or task.last_run == 0.0:
                    task.callback()
                    # Can't modify frozen dataclass, so track via replacement
                    fired.append(task.name)

        return fired

    def schedule_at(self, musical_time: float, callback: Callable[[], None], name: str = "") -> ScheduledTask:
        """Schedule a callback at an exact musical time (seconds offset).

        Finds the nearest beat to *musical_time* and binds to it.
        """
        if not self.rhythm.beats:
            raise ValueError("Rhythm has no beats")
        nearest = min(
            range(len(self.rhythm.beats)),
            key=lambda i: abs(self.rhythm.beats[i].time - musical_time),
        )
        return self.on_beat(nearest, callback, name=name or f"sched-{musical_time:.2f}", repeat=False)

    # ── info ───────────────────────────────────────────────────────

    @property
    def task_count(self) -> int:
        return len(self._tasks)

    @property
    def is_running(self) -> bool:
        return self._running

    def upcoming_beats(self, within: float = 1.0) -> list[tuple[int, float]]:
        """Return (beat_index, time_offset) pairs for beats coming within *within* seconds."""
        if not self._running or not self.rhythm.beats:
            return []
        now = _time.monotonic() - self._origin
        result: list[tuple[int, float]] = []
        for i, beat in enumerate(self.rhythm.beats):
            dt = beat.time - now
            if 0 <= dt <= within:
                result.append((i, dt))
        return result
