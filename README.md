## Generate an avatar video

Pass the avatar JSON, TTS reference audio, and its transcript:

```bash
rm -rf ./output
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

## Generate subtitles and load a new video in Remotion

The Remotion project uses files from the repository root as static assets. Give
the MP4 and SRT the same basename, then update the single configuration file
`remotion/src/video-config.ts` before previewing or rendering.

### 1. Inspect the new video

Place the MP4 in the repository root, then inspect its width, height, frame rate,
duration, and frame count. Replace `my-video.mp4` with the actual filename:

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,duration,nb_frames \
  -of default=noprint_wrappers=1 \
  "my-video.mp4"
```

The output looks similar to:

```text
width=1080
height=1920
r_frame_rate=30/1
duration=181.366667
nb_frames=5441
```

Use `nb_frames` as the Remotion `durationInFrames` value. If `nb_frames` is not
available, calculate it with:

```text
durationInFrames = ceil(duration in seconds * fps)
```

Always round up so the end of the video is not cut off.

### 2. Generate an SRT file with local Whisper

The local Whisper script accepts an MP4 directly, so extracting a separate audio
file is not required. For Chinese audio, run:

```bash
python3 whisper-asr/extract_srt.py \
  --audio "my-video.mp4" \
  --model "/home/tk/.cache/whisper/base.pt" \
  --output_file "my-video.srt" \
  --language zh
```

Available local models can be listed with:

```bash
ls ~/.cache/whisper
```

Use a larger model when it is available and valid for better recognition. For
example:

```bash
python3 whisper-asr/extract_srt.py \
  --audio "my-video.mp4" \
  --model "/home/tk/.cache/whisper/large-v3-turbo.pt" \
  --output_file "my-video.srt" \
  --language zh
```

If Whisper reports `failed finding central directory`, the selected model file
is incomplete or damaged. Use another cached model or download that model again.

Open the generated SRT and correct recognition errors against the original
script or transcript. Keep the subtitle numbers and timestamps unchanged unless
the timing is also wrong.

### 3. Configure Remotion for the new video

Edit only `remotion/src/video-config.ts`. Set `basename` without the `.mp4` or
`.srt` extension, and use the values returned by `ffprobe`:

```tsx
export const videoConfig = {
  basename: 'my-video',
  durationInFrames: 5441,
  fps: 30,
  width: 1080,
  height: 1920,
} as const;
```

For a frame rate such as `30000/1001`, use the decimal value:

```tsx
fps={30000 / 1001}
```

### 4. Preview in Remotion Studio

Install dependencies once:

```bash
cd remotion
npm install
```

Start the Studio:

```bash
npm start
```

Open the URL printed in the terminal and select `VideoWithSubtitles`. Source code
changes normally reload automatically. Changes to an SRT static asset may require
a browser refresh. If the old subtitle remains cached, stop Studio with `Ctrl+C`
and run `npm start` again.

The subtitle position and style are in
`remotion/src/VideoWithSubtitles.tsx`. In particular:

```tsx
bottom: 200,
```

A larger `bottom` value moves the subtitle up; a smaller value moves it down.

### 5. Render the final video

From the `remotion` directory, render the composition:

```bash
npm run render
```

The stable output path is `output/rendered.mp4`. To choose a different output
name for a one-off render, use the full `npx remotion render` command and pass the
desired path explicitly.

The rendered MP4 contains hard subtitles. Keep the original SRT separately if a
player-selectable subtitle track is also needed.

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
