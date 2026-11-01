import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {EventView} from './events';
import {Broll, Camera, CaptionGroup, Timeline, theme} from './types';

// Eases the teacher's frame between camera keyframes; each move springs from the previous pose.
const useCamera = (cameras: Camera[]) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  let pose = {scale: 1, x: 0, y: 0};
  for (const c of cameras) {
    if (frame < c.from) break;
    const p = spring({frame: frame - c.from, fps, config: {damping: 20, stiffness: 130, mass: 0.8}});
    pose = {
      scale: pose.scale + (c.scale - pose.scale) * p,
      x: pose.x + (c.x - pose.x) * p,
      y: pose.y + (c.y - pose.y) * p,
    };
  }
  return pose;
};

const Grid: React.FC = () => {
  const frame = useCurrentFrame();
  const shift = (frame * 0.6) % 90;
  return (
    <AbsoluteFill
      style={{
        backgroundImage: `linear-gradient(${theme.line} 1px, transparent 1px), linear-gradient(90deg, ${theme.line} 1px, transparent 1px)`,
        backgroundSize: '90px 90px',
        backgroundPosition: `${shift}px ${shift}px`,
        opacity: 0.35,
      }}
    />
  );
};

const Glow: React.FC = () => {
  const frame = useCurrentFrame();
  const x = 50 + Math.sin(frame / 55) * 22;
  const y = 42 + Math.cos(frame / 70) * 16;
  return (
    <AbsoluteFill
      style={{background: `radial-gradient(circle at ${x}% ${y}%, rgba(94,234,212,0.24), transparent 52%)`}}
    />
  );
};

const BrollLayer: React.FC<{b: Broll; src: string | null; length: number}> = ({b, src, length}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 150}});
  const exit = spring({frame: frame - (length - 10), fps, config: {damping: 20, stiffness: 170}});
  const shown = enter - exit;
  return (
    <AbsoluteFill style={{opacity: shown}}>
      {b.src ? (
        <OffthreadVideo src={staticFile(b.src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      ) : (
        <AbsoluteFill style={{backgroundColor: theme.bg}}>
          <Glow />
          <Grid />
        </AbsoluteFill>
      )}
      {b.title ? (
        <div
          style={{
            position: 'absolute',
            left: 40,
            top: 225,
            width: 810,
            color: theme.accent,
            fontFamily: theme.font,
            fontWeight: 800,
            fontSize: 44,
          }}
        >
          {b.title}
        </div>
      ) : null}
      {b.pip && src ? (
        <div
          style={{
            position: 'absolute',
            left: 610,
            top: 1010,
            width: 240,
            height: 240,
            borderRadius: 120,
            overflow: 'hidden',
            border: `5px solid ${theme.accent}`,
            transform: `scale(${enter - exit})`,
            backgroundColor: theme.bg,
          }}
        >
          <OffthreadVideo
            src={staticFile(src)}
            muted
            style={{width: 240, height: 427, objectFit: 'cover', marginTop: -40}}
          />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const Captions: React.FC<{groups: CaptionGroup[]}> = ({groups}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const g = groups.find((c) => frame >= c.f0 && frame < c.f1);
  if (!g) return null;
  const pop = spring({frame: frame - g.f0, fps, config: {damping: 16, stiffness: 220, mass: 0.6}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 40,
        top: 1250,
        width: 810,
        height: 180,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        alignContent: 'center',
        gap: '4px 16px',
        fontFamily: theme.font,
        fontWeight: 800,
        fontSize: 60,
        lineHeight: 1.12,
        transform: `scale(${0.92 + 0.08 * pop})`,
        textShadow: '0 4px 18px rgba(0,0,0,0.95), 0 0 4px rgba(0,0,0,0.95)',
      }}
    >
      {g.words.map((w, i) => (
        <span key={i} style={{color: frame >= w.f0 && frame < w.f1 ? theme.yellow : theme.ink}}>
          {w.w}
        </span>
      ))}
    </div>
  );
};

export const Reel: React.FC<Timeline> = (t) => {
  const frame = useCurrentFrame();
  const cam = useCamera(t.cameras);
  // A slow push-in keeps a static talking shot from feeling frozen.
  const drift = interpolate(frame, [0, t.durationFrames], [1, 1.035], {
    easing: Easing.bezier(0.45, 0, 0.55, 1),
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{backgroundColor: theme.bg}}>
      <AbsoluteFill
        style={{transform: `translate(${cam.x}px, ${cam.y}px) scale(${cam.scale * drift})`, transformOrigin: '50% 45%'}}
      >
        {t.src ? (
          <OffthreadVideo src={staticFile(t.src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : null}
      </AbsoluteFill>
      {t.audio ? <Audio src={staticFile(t.audio)} /> : null}
      {t.brolls.map((b, i) => (
        <Sequence key={i} from={b.from} durationInFrames={Math.max(1, b.to - b.from)} layout="none">
          <BrollLayer b={b} src={t.src} length={b.to - b.from} />
        </Sequence>
      ))}
      {t.events.map((e) => (
        <Sequence key={e.id} from={e.from} durationInFrames={Math.max(1, e.to - e.from)} layout="none">
          <EventView e={e} />
        </Sequence>
      ))}
      <Captions groups={t.captions} />
    </AbsoluteFill>
  );
};
