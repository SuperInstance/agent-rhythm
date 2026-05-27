"""Tests for agent_rhythm.scheduler"""

import time

from agent_rhythm import Rhythm, RhythmicScheduler, Beat, TimeSignature


class TestRhythmicScheduler:
    def test_register_on_beat(self):
        r = Rhythm.steady(8, bpm=120.0)
        sched = RhythmicScheduler(rhythm=r)
        fired = []
        sched.on_beat(0, lambda: fired.append(0), name="b0")
        sched.on_beat(4, lambda: fired.append(4), name="b4")
        assert sched.task_count == 2

    def test_on_downbeat(self):
        r = Rhythm.steady(16, bpm=120.0, time_signature=TimeSignature(4, 4))
        sched = RhythmicScheduler(rhythm=r)
        sched.on_downbeat(lambda: None)
        # 16 beats / 4 per bar = 4 downbeats
        assert sched.task_count == 4

    def test_on_accent(self):
        beats = [Beat(0.0, 1.0), Beat(0.5, 0.3), Beat(1.0, 0.9)]
        r = Rhythm(beats=beats)
        sched = RhythmicScheduler(rhythm=r)
        sched.on_accent(lambda: None)
        assert sched.task_count == 2  # beats 0 and 2 are accents

    def test_remove_task(self):
        r = Rhythm.steady(4, bpm=120.0)
        sched = RhythmicScheduler(rhythm=r)
        task = sched.on_beat(0, lambda: None)
        assert sched.task_count == 1
        sched.remove_task(task)
        assert sched.task_count == 0

    def test_schedule_at(self):
        r = Rhythm.steady(8, bpm=60.0)  # beats at 0,1,2,3,4,5,6,7
        sched = RhythmicScheduler(rhythm=r)
        task = sched.schedule_at(3.0, lambda: None, name="at-3")
        assert task.beat_index == 3

    def test_schedule_at_empty(self):
        sched = RhythmicScheduler(rhythm=Rhythm())
        try:
            sched.schedule_at(1.0, lambda: None)
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_tick_not_started(self):
        sched = RhythmicScheduler(rhythm=Rhythm.steady(4, bpm=120.0))
        assert sched.tick() == []

    def test_start_stop(self):
        sched = RhythmicScheduler(rhythm=Rhythm.steady(4, bpm=120.0))
        assert not sched.is_running
        sched.start()
        assert sched.is_running
        sched.stop()
        assert not sched.is_running

    def test_upcoming_beats(self):
        sched = RhythmicScheduler(rhythm=Rhythm.steady(8, bpm=120.0))
        sched.start()
        upcoming = sched.upcoming_beats(within=10.0)
        assert len(upcoming) > 0
        sched.stop()

    def test_tick_fires_task(self):
        r = Rhythm.steady(4, bpm=120.0)
        sched = RhythmicScheduler(rhythm=r, look_ahead=0.6)
        fired = []
        sched.on_beat(0, lambda: fired.append("b0"), name="b0")
        sched.start()
        # Immediately after start, beat 0 should be within look_ahead
        time.sleep(0.01)
        result = sched.tick()
        sched.stop()
        # beat 0 is at time 0.0, and we're very close to origin
        assert "b0" in result
