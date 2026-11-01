import React, {useEffect, useState} from 'react';
import {Composition, continueRender, delayRender} from 'remotion';
import '@fontsource-variable/inter/wght.css';
import 'katex/dist/katex.min.css';
import {Reel} from './Reel';
import {Timeline} from './types';

const defaults: Timeline = {
  fps: 30,
  width: 1080,
  height: 1920,
  durationFrames: 90,
  src: null,
  captions: [],
  events: [],
  cameras: [],
  brolls: [],
};

// Math must not be screenshotted before its font arrives, or formulas jump between frames.
const FONTS: Array<[string, string]> = [
  ['800 40px "Inter Variable"', 'ğüşıöçĞÜŞİÖÇ abc'],
  ['400 40px KaTeX_Main', 'x2+-='],
  ['italic 400 40px KaTeX_Math', 'xyab'],
  ['400 40px KaTeX_Size1', '('],
  ['400 40px KaTeX_Size2', '('],
];

const FontGate: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all(FONTS.map(([font, text]) => document.fonts.load(font, text)))
      .then(() => document.fonts.ready)
      .then(() => continueRender(handle))
      .catch((err) => {
        console.error(err);
        continueRender(handle);
      });
  }, [handle]);
  return <>{children}</>;
};

export const Root: React.FC = () => (
  <Composition
    id="Reel"
    component={(props: Timeline) => (
      <FontGate>
        <Reel {...props} />
      </FontGate>
    )}
    defaultProps={defaults}
    fps={30}
    width={1080}
    height={1920}
    durationInFrames={90}
    calculateMetadata={({props}) => ({
      fps: props.fps,
      width: props.width,
      height: props.height,
      durationInFrames: props.durationFrames,
    })}
  />
);
