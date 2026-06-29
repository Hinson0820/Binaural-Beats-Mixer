import argparse
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 44100
CHUNK_SIZE = int(SAMPLE_RATE)

PRESETS = {
    "delta": {"beat": 2},
    "theta": {"beat": 6},
    "alpha": {"beat": 10},
    "beta": {"beat": 20},
    "gamma": {"beat": 40},
    "theta-gamma": {"beat": 6, "f_hi": 40},
    "delta-gamma": {"beat": 2, "f_hi": 40},
    "alpha-gamma": {"beat": 10, "f_hi": 40},
    "theta-beta": {"beat": 6, "f_hi": 18},
}


def generate(carrier, beat, duration, sr, amplitude, fade,
             f_hi=None, hi_mode="binaural", mod_depth=0.5, hi_carrier=400,
             hi_mix=0.5):
    n = int(sr * duration)
    fade_n = min(int(fade * sr), n // 2)
    is_cfc = f_hi is not None and f_hi > 0

    fade_in = None
    fade_out = None
    if fade_n > 0:
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_n)))
        fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_n)))

    if is_cfc:
        norm = 1.0 / ((1.0 - hi_mix) + hi_mix * (1.0 + mod_depth))
        lo_gain = amplitude * (1.0 - hi_mix) * norm
        hi_gain = amplitude * hi_mix * norm

    for start in range(0, n, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n)
        local_n = end - start
        sample_idx = np.arange(start, end)
        t = sample_idx / sr

        left = amplitude * np.sin(2 * np.pi * (carrier - beat / 2) * t)
        right = amplitude * np.sin(2 * np.pi * (carrier + beat / 2) * t)

        if is_cfc:
            envelope = 1.0 + mod_depth * np.sin(2 * np.pi * beat * t)

            lo_left = lo_gain * np.sin(2 * np.pi * (carrier - beat / 2) * t)
            lo_right = lo_gain * np.sin(2 * np.pi * (carrier + beat / 2) * t)

            if hi_mode == "mono":
                hi_tone = np.sin(2 * np.pi * hi_carrier * t)
                hi_left = hi_gain * envelope * hi_tone
                hi_right = hi_gain * envelope * hi_tone
            else:
                hi_left = hi_gain * envelope * np.sin(2 * np.pi * (hi_carrier - f_hi / 2) * t)
                hi_right = hi_gain * envelope * np.sin(2 * np.pi * (hi_carrier + f_hi / 2) * t)

            left = lo_left + hi_left
            right = lo_right + hi_right

        chunk = np.column_stack((left, right))

        if fade_n > 0:
            mask_in = sample_idx < fade_n
            if mask_in.any():
                chunk[mask_in] *= fade_in[sample_idx[mask_in], np.newaxis]
            mask_out = sample_idx >= n - fade_n
            if mask_out.any():
                chunk[mask_out] *= fade_out[sample_idx[mask_out] - (n - fade_n), np.newaxis]

        yield chunk


def write_wav(path, chunks, sr):
    it = iter(chunks)
    first = next(it)
    data = (first * 32767).astype(np.int16)
    with wave.open(path, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(data.tobytes())
        for chunk in it:
            data = (chunk * 32767).astype(np.int16)
            f.writeframes(data.tobytes())


def parse_args():
    parser = argparse.ArgumentParser(description="Generate binaural beats")
    parser.add_argument(
        "-p", "--preset", choices=list(PRESETS.keys()),
        help="Preset (overrides --beat, and --f-hi if preset includes it)"
    )
    parser.add_argument(
        "-c", "--carrier", type=float, default=200, help="Center carrier frequency (Hz)"
    )
    parser.add_argument(
        "-b", "--beat", type=float, default=10, help="Beat frequency (Hz)"
    )
    parser.add_argument(
        "-d", "--duration", type=float, default=300, help="Duration (seconds)"
    )
    parser.add_argument(
        "-o", "--output", default="binaural.wav",
        help="Output filename (saved in output/)"
    )
    parser.add_argument(
        "-v", "--volume", type=float, default=0.5, help="Amplitude 0–1"
    )
    parser.add_argument(
        "-f", "--fade", type=float, default=0.5,
        help="Fade in/out duration (seconds)"
    )
    parser.add_argument(
        "--f-hi", type=float, default=None,
        help="High (nested) frequency for CFC mode (Hz)"
    )
    parser.add_argument(
        "--hi-mode", choices=("mono", "binaural"), default="binaural",
        help="How the high layer is presented (default: binaural)"
    )
    parser.add_argument(
        "--mod-depth", type=float, default=0.5,
        help="Modulation depth 0–1 for CFC envelope"
    )
    parser.add_argument(
        "--hi-carrier", type=float, default=400,
        help="Carrier frequency for the high layer (Hz)"
    )
    parser.add_argument(
        "--hi-mix", type=float, default=0.5,
        help="High layer mix ratio 0–1 (default: 0.5)"
    )
    args = parser.parse_args()

    if args.volume < 0 or args.volume > 1:
        parser.error("--volume must be between 0 and 1")
    if args.mod_depth < 0 or args.mod_depth > 1:
        parser.error("--mod-depth must be between 0 and 1")
    if args.hi_mix < 0 or args.hi_mix > 1:
        parser.error("--hi-mix must be between 0 and 1")

    return args


def main():
    args = parse_args()

    if args.preset:
        p = PRESETS[args.preset]
        beat = p["beat"]
        f_hi = p.get("f_hi", args.f_hi)
    else:
        beat = args.beat
        f_hi = args.f_hi

    label = f"binaural beat @ {beat} Hz"
    if f_hi:
        hi_label = "binaural" if args.hi_mode == "binaural" else "mono"
        label += f" + {hi_label} CFC @ {f_hi} Hz (depth {args.mod_depth})"

    out = Path("output", args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.duration}s {label}...")
    chunks = generate(
        args.carrier, beat, args.duration, SAMPLE_RATE, args.volume, args.fade,
        f_hi, args.hi_mode, args.mod_depth, args.hi_carrier, args.hi_mix
    )
    write_wav(str(out), chunks, SAMPLE_RATE)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
