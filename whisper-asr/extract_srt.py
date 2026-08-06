#!/usr/bin/env python3
import argparse
import sys
import os
import whisper
from whisper.utils import WriteSRT


def main():
    parser = argparse.ArgumentParser(description="Extract SRT from audio using local Whisper model")
    parser.add_argument("--audio", type=str, required=True, help="Path to input audio file")
    parser.add_argument("--model", type=str, default="base", help="Whisper model to use")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the SRT file (e.g., output/speech.srt)")
    parser.add_argument("--language", type=str, required=True, help="Language of the audio (e.g., 'zh' for Chinese, 'en' for English, 'ja' for Japanese, 'ko' for Korean, 'fr' for French, 'de' for German)")

    args = parser.parse_args()

    print(f"Loading Whisper model '{args.model}' on GPU...")
    model = whisper.load_model(args.model, device="cuda")

    print(f"Transcribing '{args.audio}'...")
    result = model.transcribe(args.audio, language=args.language)

    print("Writing SRT file...")
    with open(args.output_file, "w", encoding="utf-8") as f:
        srt_writer = WriteSRT(".")
        srt_writer.write_result(result, f)

    print(f"Extraction complete! SRT file saved to: {args.output_file}")


if __name__ == "__main__":
    main()
