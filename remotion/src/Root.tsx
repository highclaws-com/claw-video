import {Composition} from 'remotion';
import {VideoWithSubtitles} from './VideoWithSubtitles';

export const RemotionRoot = () => {
  return (
    <Composition
      id="VideoWithSubtitles"
      component={VideoWithSubtitles}
      durationInFrames={5441}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
