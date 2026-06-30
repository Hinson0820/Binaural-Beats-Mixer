# Binaural Beats Mixer

Python 3.14 single-file app at `binaural_beats.py`.
Full usage, options, and reference at **README.md**.

## Setup

- **Activate venv**: `.venv/Scripts/Activate.ps1` (Windows) / `.venv/bin/activate` (Unix)
- **Install deps**: `pip install numpy` (only dependency)
- **Run**: `python binaural_beats.py [options]`
- Python 3.14.6 (venv managed)

## Presets

| Preset | Beat | Use case |
|--------|------|----------|
| delta | 2 Hz | Deep sleep |
| theta | 6 Hz | Meditation |
| alpha | 10 Hz | Relaxed focus |
| beta | 20 Hz | Concentration |
| gamma | 40 Hz | Peak cognition |
| theta-gamma | 6 + 40 Hz | Alert meditation (CFC) |
| delta-gamma | 2 + 40 Hz | Sleep + memory (CFC) |
| alpha-gamma | 10 + 40 Hz | Flow state (CFC) |
| theta-beta | 6 + 18 Hz | Attention (CFC) |

## Architecture

- Symmetrical detune: `L = carrier - beat/2`, `R = carrier + beat/2`
- Raised-cosine (Hann) fade in/out prevents clicks
- Writes 16-bit PCM stereo WAV via stdlib `wave`
- Vectorized numpy, no loop per sample, chunked for O(1) memory
- Session mode: no inheritance — each segment starts from CLI defaults
- `seg_val()` sweeps numeric params during crossfade; `seg_val_cat()` / `seg_val_snap()` snap at boundary
- `_accumulate_phase()` carried across chunk boundaries for click-free continuity
- CFC gain normalizer: `norm = 1.0 / (lo_mix + hi_mix * (1 + mod_depth))` — peak-level consistent between simple and CFC modes

No test/lint/build config exists yet. Repo on `main`, no commits.
