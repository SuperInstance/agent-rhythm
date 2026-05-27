"""Tests for agent_rhythm.tempo"""

from agent_rhythm import TempoTracker, TempoChange


class TestTempoTracker:
    def test_global_bpm_steady(self):
        tt = TempoTracker()
        beats = [i * 0.5 for i in range(10)]  # 120 bpm
        bpm = tt.global_bpm(beats)
        assert abs(bpm - 120.0) < 1e-6

    def test_global_bpm_single(self):
        tt = TempoTracker()
        assert tt.global_bpm([0.0]) == 0.0
        assert tt.global_bpm([]) == 0.0

    def test_global_bpm_60(self):
        tt = TempoTracker()
        beats = [float(i) for i in range(5)]  # 1s apart = 60bpm
        assert abs(tt.global_bpm(beats) - 60.0) < 1e-6

    def test_instant_bpm(self):
        tt = TempoTracker()
        beats = [0.0, 0.5, 1.0]
        bpms = tt.instant_bpm(beats)
        assert len(bpms) == 2
        assert all(abs(b - 120.0) < 1e-6 for b in bpms)

    def test_detect_accelerando(self):
        tt = TempoTracker(window=3, change_threshold=0.1)
        # First 5 beats at 1s intervals (60bpm), then 5 at 0.5s (120bpm)
        beats = [float(i) for i in range(5)] + [5.0 + j * 0.5 for j in range(5)]
        accel, decel = tt.detect_acceleration(beats)
        assert len(accel) >= 1
        assert all(c.is_accelerando for c in accel)

    def test_detect_ritardando(self):
        tt = TempoTracker(window=3, change_threshold=0.1)
        # Fast then slow
        beats = [j * 0.5 for j in range(5)] + [2.5 + i * 1.0 for i in range(5)]
        accel, decel = tt.detect_acceleration(beats)
        assert len(decel) >= 1
        assert all(c.is_ritardando for c in decel)

    def test_no_changes(self):
        tt = TempoTracker()
        beats = [float(i) for i in range(20)]
        changes = tt.analyse(beats)
        assert len(changes) == 0

    def test_tempo_change_properties(self):
        tc = TempoChange(time=5.0, bpm_before=60.0, bpm_after=120.0, rate=2.0)
        assert tc.is_accelerando
        assert not tc.is_ritardando
        assert abs(tc.delta_bpm - 60.0) < 1e-9

    def test_bpm_curve(self):
        tt = TempoTracker()
        beats = [float(i) for i in range(10)]  # 1s intervals = 60 bpm
        curve = tt.bpm_curve(beats)
        assert len(curve) > 0
        for t, bpm in curve:
            assert abs(bpm - 60.0) < 1.0

    def test_rolling_bpm_short(self):
        tt = TempoTracker(window=4)
        beats = [0.0, 0.5]
        # Fewer beats than window → empty changes
        assert tt.analyse(beats) == []
