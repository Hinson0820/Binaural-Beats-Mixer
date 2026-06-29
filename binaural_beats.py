import argparse
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 44100
CHUNK_SIZE = int(SAMPLE_RATE)  # 1 second per chunk — memory is O(CHUNK_SIZE)

PRESETS = {
    "delta": 2,
    "theta": 6,
    "alpha": 10,
    "beta": 20,
    "gamma": 40,
}


def generate(carrier, beat, duration, sr, amplitude, fade):
    n = int(sr * duration)
    fade_n = min(int(fade * sr), n // 2)

    fade_in = None
    fade_out = None
    if fade_n > 0:
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_n)))
        fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_n)))

    for start in range(0, n, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n)
        local_n = end - start
        sample_idx = np.arange(start, end)
        t = sample_idx / sr

        left = amplitude * np.sin(2 * np.pi * (carrier - beat / 2) * t)
        right = amplitude * np.sin(2 * np.pi * (carrier + beat / 2) * t)
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
        "-p", "--preset", choices=PRESETS.keys(), help="Preset (overrides --beat)"
    )
    parser.add_argument(
        "-c", "--carrier", type=float, default=200, help="Center frequency in Hz"
    )
    parser.add_argument(
        "-b", "--beat", type=float, default=10, help="Beat frequency in Hz"
    )
    parser.add_argument(
        "-d", "--duration", type=float, default=300, help="Duration in seconds"
    )
    parser.add_argument(
        "-o", "--output", default="binaural.wav", help="Output filename (saved in output/)"
    )
    parser.add_argument(
        "-v", "--volume", type=float, default=0.5, help="Amplitude 0-1"
    )
    parser.add_argument(
        "-f", "--fade", type=float, default=0.5, help="Fade in/out duration in seconds"
    )
    args = parser.parse_args()

    if args.volume < 0 or args.volume > 1:
        parser.error("--volume must be between 0 and 1")

    return args


def main():
    args = parse_args()
    beat = PRESETS[args.preset] if args.preset else args.beat

    out = Path("output", args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.duration}s binaural beat @ {beat} Hz...")
    chunks = generate(args.carrier, beat, args.duration, SAMPLE_RATE, args.volume, args.fade)
    write_wav(str(out), chunks, SAMPLE_RATE)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
