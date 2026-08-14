## Generate an avatar video

Pass the avatar JSON, TTS reference audio, and its transcript:

```bash
./gen.sh avatar-taishoh.json qwen-tts/ref.mp3 qwen-tts/ref.txt
```

To produce a final video:

- Targeting phone screen 750x1334 in OBS
- Use uxplay to cast phone recording
- Use Kdenlive to edit and cut video

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
