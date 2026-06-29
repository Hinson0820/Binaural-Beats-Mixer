# Binaural Beats Mixer

Python 3.14 single-file app at `binaural_beats.py`.

## Setup

- **Activate venv**: `.venv/Scripts/Activate.ps1` (Windows) / `.venv/bin/activate` (Unix)
- **Install deps**: `pip install numpy` (only dependency)
- **Run**: `python binaural_beats.py [options]`
- Python 3.14.6 (venv managed)

## CLI

```
python binaural_beats.py -p theta -d 600 -o meditate.wav
python binaural_beats.py -c 200 -b 10 -d 300 -v 0.3
```

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --preset` | — | `delta,theta,alpha,beta,gamma` (overrides `--beat`) |
| `-c, --carrier` | 200 | Center carrier frequency (Hz) |
| `-b, --beat` | 10 | Beat frequency (Hz) |
| `-d, --duration` | 300 | Duration (seconds) |
| `-o, --output` | binaural.wav | Output filename (saved in output/) |
| `-v, --volume` | 0.5 | Amplitude 0–1 |
| `-f, --fade` | 0.5 | Fade in/out duration (seconds) |

## Presets

| Preset | Beat | Use case |
|--------|------|----------|
| delta  | 2 Hz | Deep sleep |
| theta  | 6 Hz | Meditation |
| alpha  | 10 Hz | Relaxed focus |
| beta   | 20 Hz | Concentration |
| gamma  | 40 Hz | Peak cognition |

## Output

- Generated WAV files go in `output/` (gitignored)
- Default output path is `output/binaural.wav`

## Architecture

- Symmetrical detune: `L = center - beat/2`, `R = center + beat/2`
- Raised-cosine (Hann) fade in/out prevents clicks
- Writes 16-bit PCM stereo WAV via stdlib `wave`
- Vectorized numpy, no loop per sample

No test/lint/build config exists yet. Repo on `main`, no commits.
