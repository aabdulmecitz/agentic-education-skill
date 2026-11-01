import katex from 'katex';
import React, {useLayoutEffect, useRef} from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {EventBase, theme, toneColor} from './types';

// Sequence-local frame of an absolute anchor frame.
const useProgress = (absolute: number | undefined, from: number, soft = false) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (absolute === undefined) return 1;
  return spring({
    frame: frame - (absolute - from),
    fps,
    config: soft ? {damping: 22, stiffness: 90} : {damping: 13, stiffness: 170, mass: 0.7},
  });
};

const Tex: React.FC<{latex: string}> = ({latex}) => (
  <span
    dangerouslySetInnerHTML={{
      __html: katex.renderToString(latex, {displayMode: false, throwOnError: true, strict: false}),
    }}
  />
);

// Shrinks its content to the box. Measured with layout sizes, so parent transforms do not affect it.
const Fit: React.FC<{w: number; h: number; children: React.ReactNode}> = ({w, h, children}) => {
  const ref = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const s = Math.min(1, w / el.offsetWidth, h / el.offsetHeight);
    el.style.transform = `scale(${s})`;
  });
  return (
    <div style={{width: w, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div ref={ref} style={{flex: 'none', width: 'max-content', maxWidth: w * 1.8}}>
        {children}
      </div>
    </div>
  );
};

// Enter and leave on springs, never linearly. `plain` drops the card for full-screen scenes.
const Panel: React.FC<{e: EventBase; plain?: boolean; children: React.ReactNode}> = ({e, plain, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const length = e.to - e.from;
  const enter = spring({frame, fps, config: {damping: 14, stiffness: 170, mass: 0.75}});
  const exit = spring({frame: frame - (length - 9), fps, config: {damping: 20, stiffness: 190}});
  const shown = enter - exit;
  const {x, y, w, h} = e.box;
  const color = e.tone ? toneColor(e.tone) : theme.line;
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: w,
        height: h,
        opacity: Math.min(1, shown * 1.6),
        transform: `translateY(${(1 - shown) * 34}px) scale(${0.84 + 0.16 * shown})`,
        filter: `blur(${(1 - Math.min(1, shown)) * 12}px)`,
        fontFamily: theme.font,
        color: theme.ink,
        ...(plain
          ? {}
          : {
              backgroundColor: theme.card,
              border: `3px solid ${color}`,
              borderRadius: 30,
              boxShadow: `0 18px 60px rgba(0,0,0,0.55), 0 0 40px ${e.tone ? color + '44' : 'rgba(94,234,212,0.16)'}`,
            }),
        overflow: 'hidden',
      }}
    >
      {children}
    </div>
  );
};

const pad = 26;
const inner = (e: EventBase) => ({w: e.box.w - pad * 2, h: e.box.h - pad * 2});
const Padded: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{position: 'absolute', left: pad, top: pad}}>{children}</div>
);

const Hook: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {w, h} = inner(e);
  const hookWords = (e.text as string).split(/\s+/);
  const accent = ((e.accent as string) ?? '').toLocaleLowerCase('tr').split(/\s+/);
  let index = 0;
  return (
    <Panel e={e} plain>
      <Padded>
        <Fit w={w} h={h}>
          <div style={{fontSize: 92, fontWeight: 800, lineHeight: 1.05, textAlign: 'center', width: w, textShadow: '0 6px 30px rgba(0,0,0,0.9)'}}>
            {hookWords.map((word, n) => (
              // Letters animate, but each word stays unbreakable so a line never wraps mid-word.
              <span key={n} style={{display: 'inline-block', whiteSpace: 'nowrap', marginRight: '0.26em'}}>
                {Array.from(word).map((c, i) => {
                  // Whole line is up within a third of a second: the hook has to read on first glance.
                  const p = spring({frame: frame - Math.min(index++ * 0.5, 9), fps, config: {damping: 12, stiffness: 240, mass: 0.5}});
                  return (
                    <span
                      key={i}
                      style={{
                        display: 'inline-block',
                        color: accent.includes(word.toLocaleLowerCase('tr')) ? theme.yellow : theme.ink,
                        transform: `scale(${0.55 + 0.45 * p})`,
                        filter: `blur(${(1 - Math.min(1, p)) * 7}px)`,
                      }}
                    >
                      {c}
                    </span>
                  );
                })}
              </span>
            ))}
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const TextCard: React.FC<{e: EventBase}> = ({e}) => {
  const {w, h} = inner(e);
  return (
    <Panel e={e}>
      <Padded>
        <Fit w={w} h={h}>
          <div style={{fontSize: 68, fontWeight: 800, lineHeight: 1.1, textAlign: 'center', maxWidth: w, color: toneColor(e.tone)}}>
            {e.text}
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const Strike: React.FC<{p: number}> = ({p}) => (
  <div
    style={{
      position: 'absolute',
      left: '-3%',
      top: '50%',
      width: `${106 * Math.min(1, p)}%`,
      height: 9,
      borderRadius: 5,
      backgroundColor: theme.wrong,
      transform: 'rotate(-6deg)',
      transformOrigin: 'left center',
    }}
  />
);

const Formula: React.FC<{e: EventBase}> = ({e}) => {
  const strike = useProgress(e.strike_f, e.from, true);
  const {w, h} = inner(e);
  return (
    <Panel e={e}>
      <Padded>
        <Fit w={w} h={h}>
          <div style={{position: 'relative', fontSize: 96, color: toneColor(e.tone), whiteSpace: 'nowrap'}}>
            <Tex latex={e.latex} />
            {e.strike_f !== undefined && strike > 0.001 ? <Strike p={strike} /> : null}
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const StepRow: React.FC<{e: EventBase; step: any; active: boolean; size: number}> = ({e, step, active, size}) => {
  const p = useProgress(step.f, e.from);
  const frame = useCurrentFrame();
  if (frame < step.f - e.from) return null;
  return (
    <div
      style={{
        fontSize: size,
        whiteSpace: 'nowrap',
        textAlign: 'center',
        opacity: (active ? 1 : 0.58) * Math.min(1, p),
        color: active ? toneColor(step.tone) : theme.dim,
        transform: `translateY(${(1 - p) * 26}px) scale(${0.86 + 0.14 * p})`,
      }}
    >
      <Tex latex={step.latex} />
    </div>
  );
};

const Steps: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {w, h} = inner(e);
  const absolute = frame + e.from;
  const steps: any[] = e.steps;
  let active = 0;
  steps.forEach((s, i) => {
    if (absolute >= s.f) active = i;
  });
  // Layout stays reserved for every step, so rows never reflow when a new line lands.
  return (
    <Panel e={e}>
      <Padded>
        <Fit w={w} h={h}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22}}>
            {steps.map((s, i) => (
              <div key={i} style={{minHeight: 92}}>
                <StepRow e={e} step={s} active={i === active} size={78} />
              </div>
            ))}
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const Compare: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const strike = useProgress(e.strike_f, e.from, true);
  const right = useProgress(e.right_f, e.from);
  const {w, h} = inner(e);
  const showRight = frame >= e.right_f - e.from;
  return (
    <Panel e={e}>
      <Padded>
        <Fit w={w} h={h}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 34, minWidth: w * 0.7}}>
            <div style={{position: 'relative', fontSize: 78, color: theme.wrong, whiteSpace: 'nowrap'}}>
              <Tex latex={e.wrong} />
              {strike > 0.001 && e.strike_f !== undefined ? <Strike p={strike} /> : null}
            </div>
            <div
              style={{
                fontSize: 78,
                color: theme.right,
                whiteSpace: 'nowrap',
                visibility: showRight ? 'visible' : 'hidden',
                opacity: Math.min(1, right),
                transform: `scale(${0.7 + 0.3 * right})`,
              }}
            >
              <Tex latex={e.right} />
            </div>
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const Quiz: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const answer = useProgress(e.answer_f, e.from);
  const {w, h} = inner(e);
  const seconds: number = e.seconds;
  const t = interpolate(frame, [0, seconds * fps], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.3, 0.1, 0.7, 0.9),
  });
  const left = Math.max(0, Math.ceil(seconds - frame / fps));
  const showAnswer = e.answer_f !== undefined && frame >= e.answer_f - e.from;
  const R = 62;
  const C = 2 * Math.PI * R;
  return (
    <Panel e={e} >
      <Padded>
        <Fit w={w} h={h}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22, maxWidth: w}}>
            {e.label ? <div style={{fontSize: 44, fontWeight: 800, color: theme.accent, textAlign: 'center'}}>{e.label}</div> : null}
            {e.latex ? <div style={{fontSize: 86, whiteSpace: 'nowrap'}}><Tex latex={e.latex} /></div> : null}
            {showAnswer ? (
              <div style={{fontSize: 86, color: theme.right, whiteSpace: 'nowrap', transform: `scale(${0.7 + 0.3 * answer})`}}>
                <Tex latex={e.answer} />
              </div>
            ) : (
              <svg width={150} height={150}>
                <circle cx={75} cy={75} r={R} fill="none" stroke={theme.line} strokeWidth={11} />
                <circle
                  cx={75}
                  cy={75}
                  r={R}
                  fill="none"
                  stroke={theme.yellow}
                  strokeWidth={11}
                  strokeLinecap="round"
                  strokeDasharray={C}
                  strokeDashoffset={C * t}
                  transform="rotate(-90 75 75)"
                />
                <text x={75} y={93} textAnchor="middle" fontSize={54} fontWeight={800} fill={theme.ink} fontFamily={theme.font}>
                  {left}
                </text>
              </svg>
            )}
          </div>
        </Fit>
      </Padded>
    </Panel>
  );
};

const NumberLine: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const W = e.box.w;
  const H = e.box.h;
  const y = H * 0.62;
  const X = (v: number) => 44 + ((v - e.min) / (e.max - e.min)) * (W - 88);
  const draw = spring({frame, fps, config: {damping: 22, stiffness: 90}});
  const ticks: number[] = [];
  for (let v = e.min; v <= e.max + 1e-9; v += e.step ?? 1) ticks.push(Number(v.toFixed(6)));
  const size = ticks.length > 12 ? 24 : 34;
  return (
    <Panel e={e}>
      <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0}} fontFamily={theme.font}>
        <line x1={X(e.min)} x2={X(e.min) + (X(e.max) - X(e.min)) * draw} y1={y} y2={y} stroke={theme.ink} strokeWidth={5} strokeLinecap="round" />
        {ticks.map((v, i) => (
          <g key={i} opacity={draw}>
            <line x1={X(v)} x2={X(v)} y1={y - 13} y2={y + 13} stroke={theme.ink} strokeWidth={4} />
            <text x={X(v)} y={y + 54} textAnchor="middle" fontSize={size} fontWeight={700} fill={v === 0 ? theme.accent : theme.dim}>
              {String(v).replace('-', '−')}
            </text>
          </g>
        ))}
        {(e.hops ?? []).map((hop: any, i: number) => {
          const p = spring({frame: frame - (hop.f - e.from), fps, config: {damping: 20, stiffness: 110}});
          if (frame < hop.f - e.from) return null;
          const a = X(hop.start);
          const b = X(hop.end);
          const top = y - Math.min(H * 0.42, 60 + Math.abs(b - a) * 0.34);
          const d = `M ${a} ${y - 14} Q ${(a + b) / 2} ${top} ${b} ${y - 14}`;
          return (
            <g key={i}>
              <path d={d} fill="none" stroke={theme.yellow} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p)} />
              {hop.label ? (
                <text x={(a + b) / 2} y={(y + top) / 2 - 14} textAnchor="middle" fontSize={38} fontWeight={800} fill={theme.yellow} opacity={p}>
                  {hop.label}
                </text>
              ) : null}
            </g>
          );
        })}
        {(e.points ?? []).map((pt: any, i: number) => {
          const p = spring({frame: frame - (pt.f - e.from), fps, config: {damping: 11, stiffness: 190}});
          if (frame < pt.f - e.from) return null;
          return (
            <g key={i}>
              <circle cx={X(pt.v)} cy={y} r={15 * p} fill={toneColor(pt.tone ?? 'accent')} />
              {pt.label ? <text x={X(pt.v)} y={y - 34} textAnchor="middle" fontSize={40} fontWeight={800} fill={toneColor(pt.tone ?? 'accent')} opacity={p}>{pt.label}</text> : null}
            </g>
          );
        })}
      </svg>
    </Panel>
  );
};

const Graph: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const W = e.box.w;
  const H = e.box.h;
  const m = 34;
  const X = (v: number) => m + ((v - e.xmin) / (e.xmax - e.xmin)) * (W - 2 * m);
  const Y = (v: number) => H - m - ((v - e.ymin) / (e.ymax - e.ymin)) * (H - 2 * m);
  const axes = spring({frame, fps, config: {damping: 22, stiffness: 100}});
  return (
    <Panel e={e}>
      <svg width={W} height={H} style={{position: 'absolute', left: 0, top: 0}} fontFamily={theme.font}>
        <line x1={m} x2={W - m} y1={Y(Math.max(e.ymin, Math.min(e.ymax, 0)))} y2={Y(Math.max(e.ymin, Math.min(e.ymax, 0)))} stroke={theme.dim} strokeWidth={3} opacity={axes} />
        <line y1={m} y2={H - m} x1={X(Math.max(e.xmin, Math.min(e.xmax, 0)))} x2={X(Math.max(e.xmin, Math.min(e.xmax, 0)))} stroke={theme.dim} strokeWidth={3} opacity={axes} />
        {e.curves.map((c: any, i: number) => {
          const p = interpolate(frame - (c.f - e.from), [0, 1.1 * fps], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.bezier(0.22, 1, 0.36, 1),
          });
          if (p <= 0) return null;
          const d = c.samples
            .map((s: [number, number | null], j: number) => (s[1] === null ? '' : `${j === 0 || c.samples[j - 1][1] === null ? 'M' : 'L'} ${X(s[0]).toFixed(1)} ${Y(s[1]).toFixed(1)}`))
            .join(' ');
          return <path key={i} d={d} fill="none" stroke={toneColor(c.tone ?? 'accent')} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />;
        })}
        {(e.points ?? []).map((pt: any, i: number) => {
          const p = spring({frame: frame - (pt.f - e.from), fps, config: {damping: 11, stiffness: 190}});
          if (frame < pt.f - e.from) return null;
          return (
            <g key={i}>
              <circle cx={X(pt.x)} cy={Y(pt.y)} r={13 * p} fill={theme.yellow} />
              {pt.label ? <text x={X(pt.x) + 20} y={Y(pt.y) - 18} fontSize={34} fontWeight={800} fill={theme.yellow} opacity={p}>{pt.label}</text> : null}
            </g>
          );
        })}
      </svg>
    </Panel>
  );
};

const Shape: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [vw, vh]: [number, number] = e.view;
  const margin = 30;
  const s = Math.min((e.box.w - 2 * margin) / vw, (e.box.h - 2 * margin) / vh);
  const ox = (e.box.w - vw * s) / 2;
  const oy = (e.box.h - vh * s) / 2;
  const P = (x: number, y: number) => [ox + x * s, oy + y * s];
  return (
    <Panel e={e}>
      <svg width={e.box.w} height={e.box.h} style={{position: 'absolute', left: 0, top: 0}} fontFamily={theme.font}>
        {e.items.map((it: any, i: number) => {
          const local = frame - (it.f - e.from);
          if (local < 0) return null;
          const p = spring({frame: local, fps, config: {damping: 18, stiffness: 120}});
          const stroke = toneColor(it.tone ?? 'accent');
          if (it.kind === 'label') {
            const [x, y] = P(it.x, it.y);
            return <text key={i} x={x} y={y} textAnchor="middle" fontSize={it.size ?? 40} fontWeight={800} fill={stroke} opacity={Math.min(1, p)}>{it.text}</text>;
          }
          if (it.kind === 'circle') {
            const [x, y] = P(it.cx, it.cy);
            return <circle key={i} cx={x} cy={y} r={it.r * s} fill={it.fill ? stroke + '33' : 'none'} stroke={stroke} strokeWidth={6} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p)} />;
          }
          const pts = it.pts.map(([x, y]: [number, number]) => P(x, y).join(',')).join(' ');
          return it.kind === 'line' ? (
            <polyline key={i} points={pts} fill="none" stroke={stroke} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p)} />
          ) : (
            <polygon key={i} points={pts} fill={it.fill ? stroke + '33' : 'none'} fillOpacity={Math.min(1, p)} stroke={stroke} strokeWidth={6} strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p)} />
          );
        })}
      </svg>
    </Panel>
  );
};

const FractionBars: React.FC<{e: EventBase}> = ({e}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const bars: any[] = e.bars;
  const W = e.box.w - 150;
  const rowH = Math.min(120, (e.box.h - 50) / bars.length - 18);
  return (
    <Panel e={e}>
      <div style={{position: 'absolute', left: 24, top: 25, display: 'flex', flexDirection: 'column', gap: 18}}>
        {bars.map((b, i) => {
          const local = frame - (b.f - e.from);
          const p = spring({frame: local, fps, config: {damping: 16, stiffness: 130}});
          if (local < 0) return <div key={i} style={{height: rowH}} />;
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 18, height: rowH}}>
              <div style={{width: W, height: rowH, display: 'flex', gap: 4, transform: `scaleX(${Math.min(1, p)})`, transformOrigin: 'left'}}>
                {Array.from({length: b.d}).map((_, j) => {
                  const fill = spring({frame: local - 6 - j * 2, fps, config: {damping: 18, stiffness: 150}});
                  return (
                    <div key={j} style={{flex: 1, borderRadius: 8, border: `3px solid ${theme.line}`, backgroundColor: j < b.n ? `rgba(94,234,212,${0.85 * Math.min(1, fill)})` : 'transparent'}} />
                  );
                })}
              </div>
              <div style={{fontSize: 52, opacity: Math.min(1, p)}}>
                <Tex latex={`\\frac{${b.n}}{${b.d}}`} />
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
};

const VIEWS: Record<string, React.FC<{e: EventBase}>> = {
  hook: Hook,
  text: TextCard,
  formula: Formula,
  steps: Steps,
  compare: Compare,
  quiz: Quiz,
  numberline: NumberLine,
  graph: Graph,
  shape: Shape,
  fractionbars: FractionBars,
};

export const EventView: React.FC<{e: EventBase}> = ({e}) => {
  const View = VIEWS[e.type];
  if (!View) throw new Error(`Bilinmeyen olay tipi: ${e.type}`);
  return <View e={e} />;
};
