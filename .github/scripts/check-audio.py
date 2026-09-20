#!/usr/bin/env python3
"""Fail when a rendered WAV file is short, silent or not 16 bit.

The render commands in the workflows pass -W -s, which writes a 16 bit WAV
file. This check then proves that the engine produced sound, not that it
merely exited with status zero.

    check-audio.py FILE.wav [--min-frames N] [--min-peak F]
"""
import argparse
import sys
import wave
from array import array


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--min-frames", type=int, default=40000)
    parser.add_argument("--min-peak", type=float, default=0.4)
    args = parser.parse_args()

    with wave.open(args.file) as handle:
        frames = handle.getnframes()
        width = handle.getsampwidth()
        samples = array("h")
        samples.frombytes(handle.readframes(frames))

    if width != 2:
        print(f"expected 16 bit samples, got {width * 8} bit", file=sys.stderr)
        return 1

    peak = max(abs(sample) for sample in samples) / 32768
    print(f"{args.file}: {frames} frames, peak {peak:.3f} of full scale")

    if frames < args.min_frames:
        print(f"the render is shorter than {args.min_frames} frames", file=sys.stderr)
        return 1
    if peak < args.min_peak:
        print(f"the render is quieter than {args.min_peak} of full scale", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
