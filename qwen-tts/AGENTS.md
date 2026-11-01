# qwen-tts

Voice cloning with Qwen3-TTS (`Qwen/Qwen3-TTS-12Hz-1.7B-Base`). Run scripts with the
`longcat-video-cu124` conda env (`/mnt/hg_cache/anaconda3/envs/longcat-video-cu124/bin/python`).

## Pauses

Qwen3-TTS has no pause tag (no SSML or `<break>`). Control pauses with punctuation:

- Short pause (~200 ms): `，`
- Medium pause (~250–280 ms): `、` or `；`
- Longer pause that stays steady (~330 ms): `。……`
- Don't use `……` or `——` alone as a break. They often make no pause.
- Mid-sentence `。` gives a long pause, but its length is unpredictable.
- Use full-width Chinese punctuation for Chinese text.

For pauses over ~400 ms or an exact length, generate the segments separately and join them with
silence (`np.zeros(int(sr * ms / 1000))`). Trim each segment's edges and split only at phrase
boundaries.
