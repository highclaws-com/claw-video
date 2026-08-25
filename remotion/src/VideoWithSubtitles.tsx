import {useEffect, useState} from 'react';
import {parseSrt, type Caption} from '@remotion/captions';
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const VideoWithSubtitles = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [subtitles, setSubtitles] = useState<Caption[]>([]);
  const [handle] = useState(() => delayRender('Loading 2136.srt'));

  useEffect(() => {
    fetch(staticFile('2136.srt'))
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Could not load subtitles: ${response.status}`);
        }

        return response.text();
      })
      .then((text) => {
        setSubtitles(parseSrt({input: text}).captions);
        continueRender(handle);
      })
      .catch((error) => cancelRender(error));
  }, [handle]);

  const currentTimeMs = (frame / fps) * 1000;
  const subtitle = subtitles.find(
    (item) =>
      currentTimeMs >= item.startMs && currentTimeMs < item.endMs,
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <OffthreadVideo
        src={staticFile('2136.mp4')}
        style={{height: '100%', width: '100%', objectFit: 'cover'}}
      />

      {subtitle ? (
        <div
          style={{
            position: 'absolute',
            left: 72,
            right: 72,
            bottom: 200,
            display: 'flex',
            justifyContent: 'center',
            textAlign: 'center',
            fontFamily:
              '"Noto Sans CJK SC", "Microsoft YaHei", sans-serif',
            fontSize: 58,
            fontWeight: 700,
            lineHeight: 1.35,
            color: '#fff',
            WebkitTextStroke: '3px #000',
            paintOrder: 'stroke fill',
            textShadow: '0 4px 12px rgba(0, 0, 0, 0.75)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {subtitle.text}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
