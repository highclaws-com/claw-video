#!/usr/bin/env python3
import subprocess
import argparse
import pysrt
import os


def parse_srt(filename):
    subs = pysrt.open(filename)
    segments = []
    for sub in subs:
        # pysrt SubRipTime can be converted to seconds by getting its ordinal (milliseconds)
        start_sec = sub.start.ordinal / 1000.0
        end_sec = sub.end.ordinal / 1000.0
        segments.append({'start': start_sec, 'end': end_sec})
    return segments


def main():
    parser = argparse.ArgumentParser(description="Split WAV into chunks based on SRT boundaries")
    parser.add_argument("--audio", default="../output/speech-norm.wav", help="Input audio file")
    parser.add_argument("--srt", default="../output/speech.srt", help="Input SRT file")
    parser.add_argument("--out_dir", default="../output", help="Output directory for chunks")
    parser.add_argument("--min_duration", type=float, default=5.0, help="Target minimum chunk duration in seconds")
    parser.add_argument("--max_duration", type=float, default=12.0, help="Maximum chunk duration in seconds")
    args = parser.parse_args()

    segments = parse_srt(args.srt)
    # Group segments into continuous chunks
    chunks = []
    current_start = 0.0

    for i, seg in enumerate(segments):
        cut_point = seg['end']
        duration = cut_point - current_start

        if i + 1 < len(segments):
            next_duration = segments[i+1]['end'] - current_start
        else:
            next_duration = duration

        if duration >= args.min_duration or next_duration > args.max_duration:
            chunks.append((current_start, cut_point))
            current_start = cut_point

    # Ensure the very last chunk captures everything up to the end of the last segment (or audio)
    if current_start < segments[-1]['end']:
        chunks.append((current_start, segments[-1]['end']))

    print(f"Divided into {len(chunks)} chunks.")

    # Slice the audio using ffmpeg
    for i, (start, end) in enumerate(chunks):
        chunk_name = f"smart_chunk_{i+1:03d}.wav"
        out_path = os.path.join(args.out_dir, chunk_name)

        # Add a tiny 0.1s buffer to start/end if possible to avoid clipping exact audio boundaries
        safe_start = max(0, start - 0.1)
        safe_end = end + 0.1

        cmd = [
            "ffmpeg", "-y", "-i", args.audio,
            "-ss", str(safe_start),
            "-to", str(safe_end),
            "-c", "copy",
            out_path
        ]
        print(f"Generating {chunk_name} ({safe_start:.2f}s to {safe_end:.2f}s) ...")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Done! The chunks have been cleanly split along sentence boundaries.")


if __name__ == "__main__":
    main()
