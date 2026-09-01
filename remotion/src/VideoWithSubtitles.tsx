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
import {subtitleFile, videoFile} from './video-config';

export const VideoWithSubtitles = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [subtitles, setSubtitles] = useState<Caption[]>([]);
  const [handle] = useState(() => delayRender(`Loading ${subtitleFile}`));

  useEffect(() => {
    fetch(staticFile(subtitleFile))
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
        src={staticFile(videoFile)}
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
            fontSize: 54,
            fontWeight: 700,
            lineHeight: 1.35,
            color: '#fff',
            WebkitTextStroke: '1.5px rgba(0, 0, 0, 0.85)',
            paintOrder: 'stroke fill',
            textShadow: '0 4px 12px rgba(0, 0, 0, 0.75)',
            whiteSpace: 'pre-wrap',
          }}
        >
          <span
            style={{
              padding: '18px 30px 20px',
              borderRadius: 24,
              background: 'rgba(8, 10, 15, 0.78)',
              border: '1px solid rgba(255, 255, 255, 0.18)',
              boxShadow: '0 10px 32px rgba(0, 0, 0, 0.38)',
              backdropFilter: 'blur(8px)',
            }}
          >
            {subtitle.text}
          </span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
