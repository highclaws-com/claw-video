## Generate an avatar video

Pass the avatar JSON, TTS reference audio, and its transcript:

```bash
./gen.sh avatar-taishoh.json qwen-tts/ref.mp3 qwen-tts/ref.txt
```

To produce a final video:

- Targeting phone screen 750x1334 in OBS
- Use uxplay to cast phone recording
- Use Kdenlive to edit and cut video

## Extract and denoise audio

Extract an MP3 audio track from a video:

```bash
ffmpeg -i input.mp4 -vn output.mp3
```

Place the model checkpoint at:

```text
clearer-voice/checkpoints/MossFormer2_SE_48K/
├── last_best_checkpoint
└── last_best_checkpoint.pt
```

Install the dependencies once when setting up a new Python environment:

```bash
pip install -r clearer-voice/requirements.txt
```

The checkpoint path is relative to the current working directory, so run the
CLI from the `clearer-voice` directory:

```bash
cd clearer-voice
python cli.py /path/to/input.mp3 /path/to/output.mp3
```

## SSHFS mount

```bash
sshfs user@host:/remote/path /mnt/remote \
    -o reconnect \
    -o ServerAliveInterval=15 \
    -o ServerAliveCountMax=3 \
    -o dir_cache=no \
    -o entry_timeout=0 \
    -o attr_timeout=0 \
    -o negative_timeout=0 \
    -o direct_io
```
