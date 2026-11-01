export type Box = {x: number; y: number; w: number; h: number};

export type Timed = {f: number};

export type EventBase = {
  id: string;
  type: string;
  from: number;
  to: number;
  box: Box;
  [key: string]: any;
};

export type Camera = {from: number; scale: number; x: number; y: number};

export type Broll = {from: number; to: number; src?: string; pip: boolean; title?: string; focus?: [number, number]};

export type Word = {w: string; f0: number; f1: number};

export type CaptionGroup = {f0: number; f1: number; words: Word[]};

export type Timeline = {
  fps: number;
  width: number;
  height: number;
  durationFrames: number;
  src: string | null;
  audio?: string | null;
  captions: CaptionGroup[];
  events: EventBase[];
  cameras: Camera[];
  brolls: Broll[];
};

export const theme = {
  bg: '#0B0F14',
  card: 'rgba(11, 15, 20, 0.84)',
  line: 'rgba(255, 255, 255, 0.16)',
  ink: '#F5F7FA',
  dim: '#A7B0BC',
  accent: '#5EEAD4',
  wrong: '#FB7185',
  right: '#4ADE80',
  yellow: '#FACC15',
  font: '"Inter Variable", system-ui, sans-serif',
};

export const toneColor = (tone?: string): string =>
  tone === 'wrong' ? theme.wrong : tone === 'right' ? theme.right : tone === 'accent' ? theme.accent : theme.ink;
