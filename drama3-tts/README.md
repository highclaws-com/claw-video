# drama3-tts

Voice cloning with [Fish Audio Drama 3](https://huggingface.co/fishaudio/drama-3)
(`fishaudio/drama-3`). `clone.py` works as a drop-in replacement for `qwen-tts/clone.py`: it
takes the same arguments, reads the same input files, and writes the same outputs.

Drama 3 is a 35B-A3B MoE model (3B parameters active per token). It needs about 41 GB of
GPU memory in FP8, so `clone.py` splits it across four 16 GB GPUs.

## Layout

```text
drama3-tts/
├── clone.py           # TTS script (same CLI as qwen-tts/clone.py)
├── requirements.txt   # extra pip packages
├── fish-speech/       # git submodule: github.com/fishaudio/fish-speech (inference code)
├── checkpoints/       # model weights, git-ignored, downloaded in step 3
│   └── drama-3/
├── ref.mp3, ref.txt   # reference voice and its transcript
└── input-short.txt, input-long.txt   # text to speak
```

## Setup (once)

### 1. Get the code

```bash
git submodule update --init drama3-tts/fish-speech
```

### 2. Python environment

Use the existing `longcat-video-cu124` conda env. Don't create a new one. It already has
torch 2.6 (CUDA 12.4), torchaudio, transformers and the other base packages. Install the few
extra packages with `--no-deps`:

```bash
conda activate longcat-video-cu124
pip install --no-deps -r drama3-tts/requirements.txt
```

`--no-deps` matters here. Without it, pip would downgrade the env's `protobuf` to the
`<3.20` that `descript-audiotools` pins, and that breaks `onnx` and `streamlit`. Drama 3
works fine with the newer protobuf.

### 3. Download the checkpoint (~41.5 GB)

```bash
hf download fishaudio/drama-3 --local-dir drama3-tts/checkpoints/drama-3
```

It took about 2 hours on this machine. If it gets interrupted, rerun the same command and
it picks up where it stopped. The folder should end up with `config.json`, `codec.pth`,
`tokenizer.json` and `model-000{01..15}-of-00015.safetensors`.

The repo ships its own `codec.pth`, so you don't need the S2-Pro checkpoint.

## Generate TTS

Same arguments as `qwen-tts/clone.py`:

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
CUDA_VISIBLE_DEVICES=0,1,3,4 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
python drama3-tts/clone.py \
    --text_file drama3-tts/input-long.txt --language Chinese \
    --ref_audio drama3-tts/ref.mp3 --ref_text drama3-tts/ref.txt \
    --output output/speech.wav
```

**Inputs**
- `--text_file`: the text to speak. Separate paragraphs with a blank line; each paragraph is
  generated as one chunk.
- `--ref_audio`: a 5–15 s clip of the target voice.
- `--ref_text`: the exact transcript of that clip. Unlike Qwen, Drama 3 always needs it,
  because it has no speaker-embedding-only mode.
- `--language`: accepted only so existing commands keep working. Drama 3 detects the
  language from the text.

**Outputs**
- `output/chunk_001.wav`, `chunk_002.wav`, …: one file per paragraph, at 44.1 kHz mono.
- `output/speech.wav`: all chunks joined.

If a chunk file already exists, the script skips generating it. To regenerate one
paragraph, delete its `chunk_NNN.wav` and rerun.

**Optional flags**
- `--device`: the GPUs to use (default `cuda:0,cuda:1,cuda:2,cuda:3`). The last one also
  holds the audio decoder and codec.
- `--seed N`: makes the output reproducible.
- `--checkpoint DIR`: use a different checkpoint folder.
- `--temperature` / `--top_p` / `--top_k`: sampling settings, default `1.0` / `0.9` / `30`.
  See "Sampling settings" below.
- `--reference_sampling`: switch to Fish's own Drama 3 sampling mode instead.

### GPUs on this machine

Always set `CUDA_DEVICE_ORDER=PCI_BUS_ID`. Without it, CUDA numbers the GPUs differently from
`nvidia-smi`, and `CUDA_VISIBLE_DEVICES=0,1,3,4` picks up the RTX 5070 Ti (`nvidia-smi` GPU 2).
The env's torch 2.6 build doesn't support that card (sm_120), so the run fails with `no kernel
image is available`. Use the four RTX 4070 Ti SUPERs: 0, 1, 3, 4.

Peak memory is about 11.7 / 11.5 / 11.6 / 6.2 GB on the four GPUs. Generation runs at about
8.5 frames/s (one frame is about 47 ms of audio), so speech takes roughly 2.4× its own length
to generate.

## Switching gen.sh from Qwen to Drama 3

In the TTS step of `gen.sh`, replace the `qwen-tts/clone.py` call with:

```bash
	CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0,1,3,4 \
	PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
	python drama3-tts/clone.py \
	--text_file drama3-tts/input-long.txt --language Chinese \
	--ref_audio "$TTS_REF_AUDIO" --ref_text "$TTS_REF_TEXT" \
	--output "$OUTPUT_DIR/speech.wav"
```

The rest of the pipeline (loudnorm, Whisper SRT, chunk split) reads `output/speech.wav` as it
did before. Drama 3 writes 44.1 kHz audio and Qwen writes 24 kHz. Nothing later in the pipeline
depends on the sample rate.

Drama 3 uses the same four GPUs (0,1,3,4) as the avatar step later in `gen.sh`. The steps run one
after another, so there's no conflict.

## Emotion and delivery tags

`clone.py` passes the input text to Drama 3 unchanged, so you write emotion directly into
`input-long.txt` in Drama 3's own `[...]` tag format. There's no extra syntax to learn. A tag
can go anywhere in a paragraph and affects the speech that follows it:

```text
[埋怨中带点愤怒] 你去哪里了，why you come back so late!

[whisper] 这件事千万别告诉别人。

算了，[sighs] 就这样吧。[laughs]
```

- **What can go in a tag:** free-form descriptions in Chinese or English, such as
  `[埋怨中带点愤怒]` or `[用非常愤怒的语气大声说]`. Short event tags work too, e.g.
  `[sighs]`, `[laughs]`, `[whisper]`, `[pause]`, `[emphasis]`.
- **Which works better:** in our tests, Chinese descriptions worked better than short English
  emotion tags. The exception was whispering, where `[whisper]` worked best.
- **Scope:** a tag affects the paragraph it's in, because each blank-line-separated paragraph is
  generated on its own. To use an emotion again in a later paragraph, write the tag again.
- **Long paragraphs:** Drama 3 cuts any paragraph over about 300 bytes (about 100 Chinese
  characters) into pieces and generates them one after another. Each piece hears the previous
  one, but the tag text itself only goes to the first piece. Keep emotional paragraphs short,
  or repeat the tag partway through.
- **Use `[...]`, not `(...)`.** Drama 3 has no special meaning for parentheses and will
  probably read them aloud.

The tags work on some seeds and not others, so treat them as a hint and regenerate if a line
doesn't land. The reference clip's own delivery (`ref.mp3` sounds fairly sad) also pulls every
line toward that tone. Strong emotion moves the voice slightly away from the reference.

### Sampling settings

`clone.py` defaults to temperature 1.0, top_p 0.9, top_k 30, which are the settings on the
Drama 3 model card. We compared three settings on the tagged `input-long.txt`:

| Setting | Flags | Result |
|---|---|---|
| fish-speech default | `--temperature 0.7 --top_p 0.7` | Flat. Only `[laughs]` came through clearly |
| **Model card (our default)** | none | Most expressive. Sigh, whisper and laugh all came through |
| Fish reference sampling | `--reference_sampling --temperature 1.0 --top_p 1.0 --top_k 0` | Flatter than the default, and the laugh dropped out |

Higher temperature makes the delivery more expressive, but also less stable. If a line comes
out garbled or strange, delete its `chunk_NNN.wav` and rerun, or lower `--temperature`.

## License

The Drama 3 weights use the [Fish Audio Community License](https://huggingface.co/fishaudio/drama-3/blob/main/LICENSE).
Read it before using the output commercially.
