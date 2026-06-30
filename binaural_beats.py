import argparse
import json
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


def _accumulate_phase(phi_start, freq, sr):
    """Vectorized phase accumulation for one chunk.

    freq is an array of per-sample instantaneous frequencies.
    Returns (samples, phi_end) where phi_end is the phase at the end
    of the chunk (ready for the next chunk).
    """
    dphi = 2 * np.pi * freq / sr
    phi = phi_start + np.concatenate([[0.0], np.cumsum(dphi[:-1])])
    return phi, phi[-1] + dphi[-1]


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

    phi_carrier = 0.0
    phi_beat = 0.0
    phi_hi_carrier = 0.0
    phi_hi_beat = 0.0

    for start in range(0, n, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n)
        local_n = end - start

        f_carrier = np.full(local_n, carrier)
        f_beat = np.full(local_n, beat / 2)

        phi_c, phi_c_end = _accumulate_phase(phi_carrier, f_carrier, sr)
        phi_b, phi_b_end = _accumulate_phase(phi_beat, f_beat, sr)
        phi_carrier, phi_beat = phi_c_end, phi_b_end

        left = amplitude * np.sin(phi_c - phi_b)
        right = amplitude * np.sin(phi_c + phi_b)

        if is_cfc:
            envelope = 1.0 + mod_depth * np.sin(2 * np.pi * beat * (start + np.arange(local_n)) / sr)

            lo_left = lo_gain * np.sin(phi_c - phi_b)
            lo_right = lo_gain * np.sin(phi_c + phi_b)

            if hi_mode == "iso":
                f_pulse = np.full(local_n, f_hi)
                f_carrier_iso = np.full(local_n, hi_carrier)
                phi_hc, phi_hc_end = _accumulate_phase(phi_hi_carrier, f_carrier_iso, sr)
                phi_p, phi_p_end = _accumulate_phase(phi_hi_beat, f_pulse, sr)
                phi_hi_carrier, phi_hi_beat = phi_hc_end, phi_p_end
                gamma_pulse = 0.5 * (1.0 + np.sin(phi_p))
                hi_left = hi_gain * envelope * gamma_pulse * np.sin(phi_hc)
                hi_right = hi_gain * envelope * gamma_pulse * np.sin(phi_hc)
            else:
                f_hi_c = np.full(local_n, hi_carrier)
                f_hi_b = np.full(local_n, f_hi)
                phi_hc, phi_hc_end = _accumulate_phase(phi_hi_carrier, f_hi_c, sr)
                phi_hb, phi_hb_end = _accumulate_phase(phi_hi_beat, f_hi_b, sr)
                phi_hi_carrier, phi_hi_beat = phi_hc_end, phi_hb_end
                hi_left = hi_gain * envelope * np.sin(phi_hc - phi_hb)
                hi_right = hi_gain * envelope * np.sin(phi_hc + phi_hb)

            left = lo_left + hi_left
            right = lo_right + hi_right

        chunk = np.column_stack((left, right))

        if fade_n > 0:
            sample_idx = np.arange(start, end)
            mask_in = sample_idx < fade_n
            if mask_in.any():
                chunk[mask_in] *= fade_in[sample_idx[mask_in], np.newaxis]
            mask_out = sample_idx >= n - fade_n
            if mask_out.any():
                chunk[mask_out] *= fade_out[sample_idx[mask_out] - (n - fade_n), np.newaxis]

        yield chunk


def generate_session(segments, crossfade, sr, amplitude, fade):
    seg_n = [int(sr * s["duration"]) for s in segments]
    seg_limits = np.cumsum([0] + seg_n)
    n = seg_limits[-1]
    fade_n = min(int(fade * sr), n // 2)
    cross_n = int(crossfade * sr)

    fade_in = None
    fade_out = None
    if fade_n > 0:
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_n)))
        fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_n)))

    def seg_val(t, seg_idx, key):
        """Return per-sample parameter values for a segment index array.

        During crossfade at segment start, linearly sweep from the
        previous segment's value. Handles None → value (sweep from 0)
        and value → None (sweep to 0).
        """
        result = np.empty(len(t))
        prev_val = None
        prev_had = False
        for i, seg in enumerate(segments):
            mask = seg_idx == i
            if not mask.any():
                continue
            val = seg.get(key)
            had = val is not None
            if i == 0 or cross_n == 0 or not prev_had:
                result[mask] = val if had else 0
            elif not had:
                # Previous had a value, this one doesn't — sweep to 0
                local_t = t[mask] - seg_limits[i] / sr
                frac = np.clip(local_t / crossfade, 0, 1)
                result[mask] = prev_val * (1 - frac)
            else:
                # Both have values — sweep between them
                local_t = t[mask] - seg_limits[i] / sr
                frac = np.clip(local_t / crossfade, 0, 1)
                result[mask] = prev_val + (val - prev_val) * frac
            prev_val = val if had else 0
            prev_had = had
        return result

    def seg_val_cat(key, seg_idx, default="binaural"):
        """Return per-sample categorical parameter values (no sweep)."""
        result = np.full(len(seg_idx), default, dtype=object)
        for i, seg in enumerate(segments):
            mask = seg_idx == i
            if mask.any():
                val = seg.get(key)
                if val is not None:
                    result[mask] = val
        return result

    phi_carrier = 0.0
    phi_beat = 0.0
    phi_hi_carrier = 0.0
    phi_hi_beat = 0.0

    for start in range(0, n, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n)
        local_n = end - start
        sample_idx = np.arange(start, end)
        t = sample_idx / sr
        seg_idx = np.searchsorted(seg_limits, sample_idx, side="right") - 1
        t_local = t - seg_limits[seg_idx] / sr

        beat_arr = seg_val(t, seg_idx, "beat")
        carrier_arr = seg_val(t, seg_idx, "carrier")
        f_hi_arr = seg_val(t, seg_idx, "f_hi")
        hi_carrier_arr = seg_val(t, seg_idx, "hi_carrier")
        mod_depth_arr = seg_val(t, seg_idx, "mod_depth")
        hi_mix_arr = seg_val(t, seg_idx, "hi_mix")
        hi_mode_arr = seg_val_cat("hi_mode", seg_idx)

        phi_c, phi_c_end = _accumulate_phase(phi_carrier, carrier_arr, sr)
        phi_b, phi_b_end = _accumulate_phase(phi_beat, beat_arr / 2, sr)
        phi_carrier, phi_beat = phi_c_end, phi_b_end

        # Always compute CFC formula — non-CFC segments default params to 0,
        # making hi_gain=0 and f_hi=0, so both layers collapse to simple binaural.
        lo_mix = 1.0 - hi_mix_arr
        denom = lo_mix + hi_mix_arr * (1.0 + mod_depth_arr)
        norm = np.where(denom > 0, 1.0 / denom, 1.0)
        lo_gain = amplitude * lo_mix * norm
        hi_gain = amplitude * hi_mix_arr * norm

        lo_left = lo_gain * np.sin(phi_c - phi_b)
        lo_right = lo_gain * np.sin(phi_c + phi_b)

        envelope = 1.0 + mod_depth_arr * np.sin(2 * np.pi * beat_arr * t)

        mask_bi = hi_mode_arr == "binaural"
        mask_iso = ~mask_bi
        hi_left = np.zeros(local_n)
        hi_right = np.zeros(local_n)

        if mask_bi.any():
            phi_hc, phi_hc_end = _accumulate_phase(phi_hi_carrier, hi_carrier_arr, sr)
            phi_hb, phi_hb_end = _accumulate_phase(phi_hi_beat, f_hi_arr, sr)
            phi_hi_carrier, phi_hi_beat = phi_hc_end, phi_hb_end
            hi_left[mask_bi] = (hi_gain * envelope * np.sin(phi_hc - phi_hb))[mask_bi]
            hi_right[mask_bi] = (hi_gain * envelope * np.sin(phi_hc + phi_hb))[mask_bi]

        if mask_iso.any():
            phi_hc, phi_hc_end = _accumulate_phase(phi_hi_carrier, hi_carrier_arr, sr)
            phi_hp, phi_hp_end = _accumulate_phase(phi_hi_beat, f_hi_arr, sr)
            phi_hi_carrier, phi_hi_beat = phi_hc_end, phi_hp_end
            gamma_pulse = 0.5 * (1.0 + np.sin(phi_hp))
            hi_left[mask_iso] = (hi_gain * envelope * gamma_pulse * np.sin(phi_hc))[mask_iso]
            hi_right[mask_iso] = (hi_gain * envelope * gamma_pulse * np.sin(phi_hc))[mask_iso]

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
        "--hi-mode", choices=("iso", "binaural"), default="binaural",
        help="How the high layer is presented: iso=isochronic pulse, binaural=binaural beat (default: binaural)"
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
        help="High layer mix ratio 0–1 — lower = quieter high part"
    )
    parser.add_argument(
        "--session-file", type=str, default=None,
        help="JSON session file with segment definitions"
    )
    parser.add_argument(
        "--crossfade", type=float, default=30,
        help="Transition sweep duration between segments in seconds (default: 30)"
    )
    args = parser.parse_args()

    if args.volume < 0 or args.volume > 1:
        parser.error("--volume must be between 0 and 1")
    if args.mod_depth < 0 or args.mod_depth > 1:
        parser.error("--mod-depth must be between 0 and 1")
    if args.hi_mix < 0 or args.hi_mix > 1:
        parser.error("--hi-mix must be between 0 and 1")

    return args


def load_session(path, args):
    with open(path) as f:
        raw = json.load(f)

    defaults = {
        "carrier": args.carrier,
        "beat": args.beat,
        "f_hi": args.f_hi,
        "hi_mode": args.hi_mode,
        "mod_depth": args.mod_depth,
        "hi_carrier": args.hi_carrier,
        "hi_mix": args.hi_mix,
    }

    segments = []
    prev = dict(defaults)
    for i, entry in enumerate(raw):
        if "duration" not in entry:
            raise ValueError(f"Segment {i} missing 'duration'")
        if entry["duration"] <= 0:
            raise ValueError(f"Segment {i} duration must be positive")
        seg = dict(prev)
        seg.update(entry)
        segments.append(seg)
        prev = seg

    return segments


def main():
    args = parse_args()

    out = Path("output", args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.session_file:
        segments = load_session(args.session_file, args)
        total_s = sum(s["duration"] for s in segments)
        descs = [s.get("desc", f"seg {i}") for i, s in enumerate(segments)]
        print(f"Generating {total_s}s session: {' → '.join(descs)} "
              f"(crossfade {args.crossfade}s)...")
        chunks = generate_session(
            segments, args.crossfade, SAMPLE_RATE, args.volume, args.fade
        )
        write_wav(str(out), chunks, SAMPLE_RATE)
        print(f"Wrote {out}")
        return

    if args.preset:
        p = PRESETS[args.preset]
        beat = p["beat"]
        f_hi = p.get("f_hi", args.f_hi)
    else:
        beat = args.beat
        f_hi = args.f_hi

    label = f"binaural beat @ {beat} Hz"
    if f_hi:
        hi_label = "binaural" if args.hi_mode == "binaural" else "iso"
        label += f" + {hi_label} CFC @ {f_hi} Hz (depth {args.mod_depth})"

    print(f"Generating {args.duration}s {label}...")
    chunks = generate(
        args.carrier, beat, args.duration, SAMPLE_RATE, args.volume, args.fade,
        f_hi, args.hi_mode, args.mod_depth, args.hi_carrier, args.hi_mix
    )
    write_wav(str(out), chunks, SAMPLE_RATE)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
