# Binaural Beats Mixer

Generate binaural beats — stereo audio tones that encourage specific brainwave states. Requires only `numpy`.

## Quick start

```powershell
.venv\Scripts\Activate.ps1
pip install numpy
python binaural_beats.py -p alpha -d 600 -o alpha_10min.wav
```

## Frequency table

| Preset | Beat freq | Brainwave band | Associated state |
|--------|-----------|----------------|------------------|
| `delta` | 2 Hz | Delta (0.5–4 Hz) | Deep sleep |
| `theta` | 6 Hz | Theta (4–8 Hz) | Meditation, REM |
| `alpha` | 10 Hz | Alpha (8–13 Hz) | Relaxed focus |
| `beta` | 20 Hz | Beta (13–30 Hz) | Concentration |
| `gamma` | 40 Hz | Gamma (30+ Hz) | Peak cognition |

## Usage

```
python binaural_beats.py [-h] [-p PRESET] [-c CARRIER] [-b BEAT] [-d DURATION]
                         [-o OUTPUT] [-v VOLUME] [-f FADE]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --preset` | — | Preset name (overrides `--beat`) |
| `-c, --carrier` | 200 Hz | Center frequency |
| `-b, --beat` | 10 Hz | Beat (difference) frequency |
| `-d, --duration` | 300 s | Output length |
| `-o, --output` | `binaural.wav` | Output filename (saved in `output/`) |
| `-v, --volume` | 0.5 | Amplitude (0–1) |
| `-f, --fade` | 0.5 s | Fade in/out length |

### Examples

```powershell
# 10-minute theta meditation track
python binaural_beats.py -p theta -d 600 -o meditate.wav

# 5-minute alpha at 30% volume
python binaural_beats.py -p alpha -d 300 -v 0.3 -o quiet.wav

# Custom: 180 Hz carrier, 15 Hz beat, 20 minutes
python binaural_beats.py -c 180 -b 15 -d 1200 -o custom.wav

# Long fade (2 seconds) for smooth meditation entry/exit
python binaural_beats.py -p delta -f 2 -o deep_sleep.wav
```

## How it works

Each ear receives a pure sine wave at slightly different frequencies:

- Left channel: `carrier - beat/2`
- Right channel: `carrier + beat/2`

The brain perceives the difference (`beat` Hz) as a rhythmic pulse — the binaural beat. Use stereo headphones for the effect.

A raised-cosine (Hann) fade in/out prevents clicks.

All generated files go in `output/` (gitignored). Pass just a filename to `-o`, the directory is automatic.

## Requirements

- Python 3.14+
- `numpy` (only dependency)
