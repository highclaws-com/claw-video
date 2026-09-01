export const videoConfig = {
  basename: '2136',
  durationInFrames: 5441,
  fps: 30,
  width: 1080,
  height: 1920,
} as const;

export const videoFile = `${videoConfig.basename}.mp4`;
export const subtitleFile = `${videoConfig.basename}.srt`;
