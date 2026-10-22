export const videoConfig = {
  basename: '2242-3000',
  durationInFrames: 3582,
  fps: 30,
  width: 1920,
  height: 1080,
} as const;

// Subtitle layout in output pixels. Re-check against a frame of each new
// video: keep the subtitle inside the picture (above any letterbox bar) and
// clear of overlays such as the avatar picture-in-picture.
//
// 1920x1080: picture spans y=38..1042 (38px black bars), avatar PiP spans
// x=1447..1877, y=640..1042. sideMargin 500 keeps the centered box within
// x=500..1420, left of the avatar.
//
// Portrait 1080x1920 reference: {bottom: 200, sideMargin: 72, fontSize: 54}.
export const subtitleLayout = {
  bottom: 80,
  sideMargin: 500,
  fontSize: 44,
} as const;

export const videoFile = `${videoConfig.basename}.mp4`;
export const subtitleFile = `${videoConfig.basename}.srt`;
