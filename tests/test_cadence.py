"""Tests for agent_rhythm.cadence"""

from agent_rhythm import CadenceAnalyzer, CadenceResult


class TestCadenceAnalyzer:
    def test_too_few_events(self):
        ca = CadenceAnalyzer(min_events=4)
        result = ca.analyse([0.0, 1.0, 2.0])
        assert result.period is None
        assert result.confidence == 0.0

    def test_regular_cadence(self):
        # Events exactly 1s apart — very regular
        ts = [float(i) for i in range(20)]
        ca = CadenceAnalyzer(min_events=4)
        result = ca.analyse(ts)
        # All intervals identical → autocorrelation may return None, but regularity must be high
        assert result.regularity > 0.9

    def test_irregular_cadence(self):
        # Random-ish spacing
        ts = [0.0, 0.3, 1.7, 2.0, 5.5, 6.1, 9.0, 10.2, 13.0, 15.0]
        ca = CadenceAnalyzer(min_events=4)
        result = ca.analyse(ts)
        assert result.regularity < 0.9

    def test_burst_detection(self):
        # Two clusters with a big gap
        ts = [0.0, 0.1, 0.2, 0.3, 10.0, 10.1, 10.2]
        ca = CadenceAnalyzer(min_events=4, burst_gap=5.0)
        result = ca.analyse(ts)
        assert result.burst_count == 2

    def test_single_burst(self):
        ts = [float(i) for i in range(10)]
        ca = CadenceAnalyzer(min_events=4, burst_gap=5.0)
        result = ca.analyse(ts)
        assert result.burst_count == 1

    def test_mean_interval(self):
        ts = [0.0, 1.0, 2.0, 3.0, 4.0]
        ca = CadenceAnalyzer()
        result = ca.analyse(ts)
        assert abs(result.mean_interval - 1.0) < 1e-9

    def test_detect_phase(self):
        ts = [float(i) for i in range(10)]
        ca = CadenceAnalyzer(min_events=4)
        phase = ca.detect_phase(ts)
        # Perfectly regular → may or may not detect period (autocorrelation of constant = 0)
        # Just ensure no crash and correct type
        assert phase is None or isinstance(phase, float)

    def test_detect_phase_insufficient(self):
        ca = CadenceAnalyzer(min_events=4)
        assert ca.detect_phase([0.0, 1.0]) is None

    def test_annotations_default_empty(self):
        r = CadenceResult(period=1.0, confidence=0.8, regularity=0.9,
                          burst_count=1, mean_interval=1.0, std_interval=0.0)
        assert r.annotations == {}
