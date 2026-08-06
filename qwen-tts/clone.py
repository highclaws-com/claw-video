import argparse
import os
import torch
import soundfile as sf
import numpy as np
from qwen_tts import Qwen3TTSModel


def main():
    parser = argparse.ArgumentParser(description="Voice Cloning with Qwen3-TTS Base")

    parser.add_argument(
        "--text_file",
        type=str,
        required=True,
        help="Path to the input text file"
    )

    parser.add_argument(
        "--ref_audio",
        type=str,
        default="ref.wav",
        help="Path to your reference audio file"
    )

    parser.add_argument(
        "--ref_text",
        type=str,
        default=None,
        help="Text of the reference audio (required for full voice cloning)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="English",
        choices=[
            "Chinese", "English", "Japanese", "Korean", "German",
            "French", "Russian", "Portuguese", "Spanish", "Italian"
        ],
        help="Target language for generation"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./output_clone.wav",
        help="Path to save the generated output audio file"
    )

    args = parser.parse_args()
    output_dir = os.path.dirname(args.output)

    with open(args.text_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    print("Resuming download of the Base model...")
    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        revision="fd4b254389122332181a7c3db7f27e918eec64e3",
        device_map="cuda:0",
        dtype=torch.bfloat16,
    )

    # Pre-compute voice clone prompt once to avoid re-encoding ref audio every chunk
    ref_text = None
    if args.ref_text:
        with open(args.ref_text, 'r', encoding='utf-8') as f:
            ref_text = f.read().strip()
    print("Pre-computing voice clone prompt from reference audio...")
    voice_clone_prompt = model.create_voice_clone_prompt(
        ref_audio=args.ref_audio,
        ref_text=ref_text,
        x_vector_only_mode=not bool(ref_text),
    )
    print("Voice clone prompt ready.")

    all_wavs = []
    sr = None
    for i, line in enumerate(lines):
        print(f"[{i+1}/{len(lines)}] Generating TTS for: {line}")
        wavs, sample_rate = model.generate_voice_clone(
            text=line,
            language=args.language,
            voice_clone_prompt=voice_clone_prompt,
        )
        all_wavs.append(wavs[0])
        sr = sample_rate

        # Save preview for the chunk respecting the output directory
        chunk_filename = os.path.join(output_dir, f"chunk_{i+1:03d}.wav")
        sf.write(chunk_filename, wavs[0], sr)
        print(f"-> Saved preview chunk to {chunk_filename}")

    if all_wavs:
        final_wav = np.concatenate(all_wavs)
        sf.write(args.output, final_wav, sr)
        print(f"Successfully cloned voice and saved to {args.output}!")
    else:
        print("No valid text found to generate voice.")


if __name__ == "__main__":
    main()
