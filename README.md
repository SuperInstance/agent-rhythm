# agent-rhythm

Rhythm, cadence, and tempo analysis for agent behavioral patterns.

A pure-Python library (no external dependencies) for modelling rhythmic structures, detecting periodic behaviour in event streams, tracking tempo changes, recognising patterns like polyrhythms and syncopation, and scheduling tasks to musical time.

## Install

```bash
pip install agent-rhythm
```

## Quick start

```python
from agent_rhythm import Rhythm, CadenceAnalyzer, TempoTracker, PatternMatcher, RhythmicScheduler

# ── Build a rhythm ──────────────────────────────────────────
rhythm = Rhythm.steady(16, bpm=120.0)
print(rhythm)               # Rhythm(beats=16, bpm=120.0, sig=4/4)
print(rhythm.intervals())   # [0.5, 0.5, 0.5, ...]
print(rhythm.density())     # 2.0 beats/sec

# From a step-sequencer grid
rhythm = Rhythm.from_grid(
    [True, False, True, False, True, False, True, False],
    subdivision=0.25,
    bpm=120.0,
)

# ── Cadence analysis ────────────────────────────────────────
import random
timestamps = sorted(random.uniform(0, 60) for _ in range(50))
cadence = CadenceAnalyzer(min_events=4)
result = cadence.analyse(timestamps)
print(f"Period: {result.period:.2f}s  Confidence: {result.confidence:.2f}")

# ── Tempo tracking ─────────────────────────────────────────
beats = [0.0, 0.5, 1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
tracker = TempoTracker(window=3, change_threshold=0.1)
changes = tracker.analyse(beats)
for c in changes:
    print(f"Tempo change at {c.time:.1f}s: {c.bpm_before:.0f} → {c.bpm_after:.0f} BPM")
print(f"Global BPM: {tracker.global_bpm(beats):.1f}")

# ── Pattern matching ────────────────────────────────────────
matcher = PatternMatcher()
rhythm = Rhythm.steady(8, bpm=120.0)
matches = matcher.match(rhythm)
for pattern, score in matches:
    print(f"{pattern.name}: {score:.2f}")

syncopation = matcher.detect_syncopation(rhythm)
print(f"Syncopation: {syncopation:.2f}")

# ── Rhythmic scheduling ─────────────────────────────────────
rhythm = Rhythm.steady(8, bpm=120.0)
scheduler = RhythmicScheduler(rhythm=rhythm)
scheduler.on_beat(0, lambda: print("Downbeat!"), name="downbeat")
scheduler.start()
```

## Modules

| Module | Description |
|---|---|
| `rhythm.py` | Core `Rhythm`, `Beat`, and `TimeSignature` classes |
| `cadence.py` | `CadenceAnalyzer` for detecting periodic behaviour in event streams |
| `tempo.py` | `TempoTracker` with BPM detection, tempo changes, accel/decel |
| `pattern.py` | `PatternMatcher` for recognising rhythmic patterns, polyrhythms, syncopation |
| `scheduler.py` | `RhythmicScheduler` that schedules callbacks to musical time |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -q
```

## License

MIT
