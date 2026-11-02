"""
Voice cloning with Fish Audio Drama 3. Writes one chunk_NNN.wav per paragraph next to the
output file, then the joined output.

  python drama3-tts/clone.py --text_file drama3-tts/input-long.txt --language Chinese \
      --ref_audio drama3-tts/ref.mp3 --ref_text drama3-tts/ref.txt --output output/speech.wav

Emotion: the text is passed to Drama 3 unchanged, so its native inline [tags] work anywhere:

  [埋怨中带点愤怒] 你去哪里了，why you come back so late!
  算了，[sighs] 就这样吧。[laughs]
"""
import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fish-speech"))

import numpy as np
import soundfile as sf
import torch

from fish_speech.models.text2semantic.inference import (
    decode_to_audio, encode_audio, generate_long, init_model, load_codec_model,
)


def main():
    parser = argparse.ArgumentParser(description="Voice Cloning with Fish Audio Drama 3")

    parser.add_argument(
        "--text_file",
        type=str,
        required=True,
        help="Path to the input text file (paragraphs separated by a blank line)"
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
        help="Text of the reference audio (required for voice cloning)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default="English",
        help="Accepted but ignored; Drama 3 detects the language from the text"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./output_clone.wav",
        help="Path to save the generated output audio file"
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(HERE / "checkpoints" / "drama-3"),
        help="Drama 3 checkpoint directory"
    )

    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0,cuda:1,cuda:2,cuda:3",
        help="Comma-separated GPUs; the backbone is split over them, the last one also holds the "
             "audio decoder and codec. Four 16 GB GPUs are enough."
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible output"
    )

    # Defaults are the settings on Drama 3's model card (temperature 1.0, top_p 0.9, top_k 30).
    # fish-speech's own defaults (0.7 / 0.7 / 30) mostly flattened the [emotion] tags.
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Sampling temperature (default 1.0; fish-speech uses 0.7). Higher = more expressive, "
             "less stable"
    )

    parser.add_argument(
        "--top_p",
        type=float,
        default=0.9,
        help="Nucleus sampling top-p (default 0.9; fish-speech uses 0.7)"
    )

    parser.add_argument(
        "--top_k",
        type=int,
        default=30,
        help="Top-k cap (default 30); 0 = no cap, only with --reference_sampling"
    )

    parser.add_argument(
        "--reference_sampling",
        action="store_true",
        help="Use Fish Audio's reference sampling for Drama 3 (epsilon cutoff + repetition "
             "replacement). Upstream recommends it with --temperature 1.0 --top_p 1.0 --top_k 0"
    )

    args = parser.parse_args()
    output_dir = os.path.dirname(args.output)

    if not args.ref_text:
        parser.error("--ref_text is required: Drama 3 clones a voice from audio plus its transcript")

    with open(args.text_file, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    lines = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
    with open(args.ref_text, 'r', encoding='utf-8') as f:
        ref_text = f.read().strip()

    checkpoint = Path(args.checkpoint)
    if not (checkpoint / "config.json").is_file():
        sys.exit(f"Drama 3 checkpoint not found at {checkpoint}; see drama3-tts/README.md")

    print("Loading Drama 3...")
    model, _ = init_model(
        checkpoint, args.device, torch.bfloat16,
        reference_sampling="argmax" if args.reference_sampling else None,
    )
    device = str(model.device)  # the last GPU: audio decoder and codec live here
    codec = load_codec_model(checkpoint / "codec.pth", device, model.dtype)

    # Encode the reference audio once instead of for every chunk
    print("Encoding reference audio...")
    ref_codes = encode_audio(args.ref_audio, codec, device).cpu()
    print("Reference ready.")

    all_wavs = []
    sr = codec.sample_rate
    for i, line in enumerate(lines):
        chunk_filename = os.path.join(output_dir, f"chunk_{i+1:03d}.wav")
        if os.path.exists(chunk_filename):
            print(f"[{i+1}/{len(lines)}] Chunk already exists, skipping TTS for: {line}")
            wav_data, sample_rate = sf.read(chunk_filename)
            all_wavs.append(wav_data)
            sr = sample_rate
            continue

        print(f"[{i+1}/{len(lines)}] Generating TTS for: {line}")
        if args.seed is not None:
            torch.manual_seed(args.seed + i)
            torch.cuda.manual_seed_all(args.seed + i)
        codes = [
            r.codes for r in generate_long(
                model=model, device=device, decode_one_token=None, text=line,
                max_new_tokens=0,  # 0 = Drama 3's own per-chunk budget
                temperature=args.temperature, top_p=args.top_p, top_k=args.top_k,
                prompt_text=[ref_text], prompt_tokens=[ref_codes],
            ) if r.action == "sample"
        ]
        if not codes:
            print(f"!! No audio generated for chunk {i+1}, skipping")
            continue
        wav = decode_to_audio(torch.cat(codes, dim=1).to(device), codec).float().cpu().numpy()
        all_wavs.append(wav)

        # Save preview for the chunk respecting the output directory
        sf.write(chunk_filename, wav, sr)
        print(f"-> Saved preview chunk to {chunk_filename}")

    if all_wavs:
        final_wav = np.concatenate(all_wavs)
        sf.write(args.output, final_wav, sr)
        print(f"Successfully cloned voice and saved to {args.output}!")
    else:
        print("No valid text found to generate voice.")


if __name__ == "__main__":
    main()
