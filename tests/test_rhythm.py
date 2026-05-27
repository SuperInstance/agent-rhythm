"""Tests for agent_rhythm.rhythm"""

from agent_rhythm import Rhythm, Beat, TimeSignature


class TestBeat:
    def test_defaults(self):
        b = Beat(time=1.0)
        assert b.velocity == 1.0
        assert b.duration == 0.0
        assert b.is_accent
        assert not b.is_rest

    def test_rest(self):
        b = Beat(time=0.0, velocity=0.0)
        assert b.is_rest
        assert not b.is_accent


class TestTimeSignature:
    def test_simple(self):
        ts = TimeSignature(4, 4)
        assert ts.is_simple
        assert not ts.is_compound

    def test_compound(self):
        ts = TimeSignature(6, 8)
        assert ts.is_compound
        assert not ts.is_simple

    def test_bar_duration(self):
        ts = TimeSignature(4, 4)
        assert ts.bar_duration(120.0) == 2.0  # 4 beats at 120bpm = 2s

    def test_bar_duration_waltz(self):
        ts = TimeSignature(3, 4)
        assert ts.bar_duration(60.0) == 3.0


class TestRhythmConstructors:
    def test_steady(self):
        r = Rhythm.steady(8, bpm=120.0)
        assert len(r) == 8
        assert abs(r.intervals()[0] - 0.5) < 1e-9

    def test_from_intervals(self):
        r = Rhythm.from_intervals([0.5, 0.5, 0.5], bpm=120.0)
        assert len(r) == 3
        assert abs(r.beats[1].time - 0.5) < 1e-9
        assert abs(r.beats[2].time - 1.0) < 1e-9

    def test_from_grid(self):
        grid = [True, False, True, False, True, False, True, False]
        r = Rhythm.from_grid(grid, subdivision=0.25, bpm=120.0)
        assert len(r) == 4  # 4 hits
        assert abs(r.beats[1].time - 0.5) < 1e-9


class TestRhythmAnalysis:
    def test_intervals(self):
        r = Rhythm.steady(4, bpm=60.0)  # 1s apart
        ivs = r.intervals()
        assert all(abs(iv - 1.0) < 1e-9 for iv in ivs)

    def test_duration(self):
        r = Rhythm.steady(5, bpm=60.0)
        assert abs(r.duration() - 4.0) < 1e-9

    def test_density(self):
        r = Rhythm.steady(5, bpm=60.0)  # 5 beats over 4s = 1.25 beats/s
        assert abs(r.density() - 1.25) < 1e-6

    def test_accent_positions(self):
        beats = [Beat(0.0, 1.0), Beat(0.5, 0.4), Beat(1.0, 0.9)]
        r = Rhythm(beats=beats)
        assert r.accent_positions() == [0, 2]

    def test_bar_count(self):
        r = Rhythm.steady(16, bpm=120.0, time_signature=TimeSignature(4, 4))
        # 16 beats, duration = 7.5s (0 to 7.5), each bar = 2s → 3 bars
        assert r.bar_count() == 3


class TestRhythmTransforms:
    def test_quantize(self):
        beats = [Beat(0.0), Beat(0.24), Beat(0.49), Beat(0.76)]
        r = Rhythm(beats=beats)
        q = r.quantize(0.25)
        assert [b.time for b in q.beats] == [0.0, 0.25, 0.5, 0.75]

    def test_stretch(self):
        r = Rhythm.steady(4, bpm=60.0)
        s = r.stretch(2.0)
        assert abs(s.bpm - 30.0) < 1e-6
        assert abs(s.beats[-1].time - 6.0) < 1e-6

    def test_repr(self):
        r = Rhythm.steady(4, bpm=120.0)
        assert "beats=4" in repr(r)
        assert "120.0" in repr(r)
