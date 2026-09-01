import {Composition} from 'remotion';
import {VideoWithSubtitles} from './VideoWithSubtitles';
import {videoConfig} from './video-config';

export const RemotionRoot = () => {
  return (
    <Composition
      id="VideoWithSubtitles"
      component={VideoWithSubtitles}
      durationInFrames={videoConfig.durationInFrames}
      fps={videoConfig.fps}
      width={videoConfig.width}
      height={videoConfig.height}
    />
  );
};
