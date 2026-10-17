import React from 'react';
import {AbsoluteFill, Audio, Img, staticFile, Sequence, useCurrentFrame, interpolate, spring, useVideoConfig, Easing} from 'remotion';
import data from '../public/data.json';

const C = {
  bg: '#05060a', ink: '#f3f5f8', dim: '#808a99', sun: '#ffc24d', ice: '#7fd4ff',
  moss: '#9bf06b', line: '#20262f',
};
const font = 'Inter, "Helvetica Neue", Arial, sans-serif';
const mono = '"SF Mono", Menlo, monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const fade = (f, d) => interpolate(f, [0, 18, d - 18, d], [0, 1, 1, 0], clamp);
const ease = Easing.inOut(Easing.cubic);
const rnd = (i) => {const x = Math.sin(i * 731.17) * 10000; return x - Math.floor(x);};

// the map images are 240 km across, centred on the pole
const MAP = {size: 760, cx: 1290, cy: 540};
const kmToPx = (km) => (km / (2 * data.image_half_km)) * MAP.size;
const sx = (xkm) => MAP.cx + kmToPx(xkm);
const sy = (ykm) => MAP.cy - kmToPx(ykm);

const Stars = () => {
  const f = useCurrentFrame();
  const stars = React.useMemo(() => Array.from({length: 150}, (_, i) =>
    ({x: rnd(i) * 1920, y: rnd(i + 400) * 1080, s: 1 + (i % 3)})), []);
  return <AbsoluteFill style={{background: `radial-gradient(ellipse at 80% 10%, #141821 0%, ${C.bg} 60%)`}}>
    {stars.map((s, i) => <div key={i} style={{position: 'absolute', left: s.x, top: s.y, width: s.s, height: s.s,
      borderRadius: 9, background: '#fff', opacity: 0.15 + 0.4 * Math.abs(Math.sin(f / 50 + i))}} />)}
  </AbsoluteFill>;
};

const Rise = ({children, delay = 0, y = 26}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame: f - delay, fps, config: {damping: 200}});
  return <div style={{opacity: s, transform: `translateY(${(1 - s) * y}px)`}}>{children}</div>;
};
const H1 = ({children, size = 62, color = C.ink, weight = 700}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: weight, color, letterSpacing: -1.2, lineHeight: 1.15}}>{children}</div>;
const Sub = ({children, size = 30, color = C.dim}) =>
  <div style={{fontFamily: font, fontSize: size, fontWeight: 500, color, lineHeight: 1.35}}>{children}</div>;

const MapImage = ({src, opacity = 1, style}) =>
  <Img src={staticFile(src)} style={{position: 'absolute', left: MAP.cx - MAP.size / 2, top: MAP.cy - MAP.size / 2,
    width: MAP.size, height: MAP.size, opacity, ...style}} />;

const Pole = ({label = true}) => <>
  <line x1={MAP.cx - 14} y1={MAP.cy} x2={MAP.cx + 14} y2={MAP.cy} stroke="#00e5ff" strokeWidth="2" />
  <line x1={MAP.cx} y1={MAP.cy - 14} x2={MAP.cx} y2={MAP.cy + 14} stroke="#00e5ff" strokeWidth="2" />
  {label && <text x={MAP.cx + 20} y={MAP.cy - 16} fill="#00e5ff" fontSize="22" fontFamily={font}>south pole</text>}
</>;

const Scale = () => {
  const len = kmToPx(50);
  const y = MAP.cy + MAP.size / 2 + 42;
  return <g>
    <line x1={MAP.cx - MAP.size / 2} y1={y} x2={MAP.cx - MAP.size / 2 + len} y2={y} stroke={C.dim} strokeWidth="2" />
    <text x={MAP.cx - MAP.size / 2 + len / 2} y={y + 28} fill={C.dim} fontSize="20" fontFamily={mono}
      textAnchor="middle">50 km</text>
  </g>;
};

// ---------------------------------------------------------------- 1. the hook
const Hook = ({d}) => {
  const f = useCurrentFrame();
  const spin = f * 0.4;
  return <AbsoluteFill style={{opacity: fade(f, d), alignItems: 'center', justifyContent: 'center'}}>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <defs>
        <radialGradient id="moon" cx="34%" cy="32%">
          <stop offset="0%" stopColor="#d8dde6" />
          <stop offset="62%" stopColor="#7e8794" />
          <stop offset="100%" stopColor="#1a1d24" />
        </radialGradient>
      </defs>
      <circle cx={960} cy={700} r={300} fill="url(#moon)" />
      {Array.from({length: 26}, (_, i) => {
        const a = rnd(i) * Math.PI * 2, r = rnd(i + 60) * 262;
        return <circle key={i} cx={960 + Math.cos(a) * r} cy={700 + Math.sin(a) * r * 0.98}
          r={6 + rnd(i + 120) * 26} fill="#000" opacity="0.12" />;
      })}
      <circle cx={960} cy={700} r={300} fill="none" stroke="#000" strokeWidth="2" opacity="0.4" />
      <circle cx={960} cy={990} r={30} fill="none" stroke={C.sun} strokeWidth="2.5"
        opacity={0.5 + 0.5 * Math.sin(spin / 12)} />
      <text x={1010} y={998} fill={C.sun} fontSize="24" fontFamily={font}>the south pole</text>
    </svg>
    <div style={{position: 'absolute', top: 110, width: '100%', textAlign: 'center'}}>
      <Rise><H1 size={74}>Everyone is going to the same place.</H1></Rise>
      <div style={{height: 18}} />
      <Rise delay={20}><Sub size={32}>Artemis, Chang'e, every lunar base study: the Moon's south pole.</Sub></Rise>
      <div style={{height: 10}} />
      <Rise delay={34}><Sub size={32} color={C.sun}>This is a map of why.</Sub></Rise>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 2. the skyline
const Skyline = ({d}) => {
  const f = useCurrentFrame();
  const rays = Math.round(interpolate(f, [60, 230], [0, 60], {...clamp, easing: ease}));
  const cx = 660, cy = 640, Rpx = 330;
  const drop = interpolate(f, [300, 380], [0, 1], clamp);
  // a terrain profile out to 100 km, and the curve of the Moon under it
  const prof = React.useMemo(() => Array.from({length: 120}, (_, i) => {
    const x = i / 119;
    return 0.42 * Math.sin(x * 7.1) + 0.3 * Math.sin(x * 17.3 + 1) + 0.2 * Math.sin(x * 31 + 2);
  }), []);
  const PX0 = 1130, PX1 = 1810, PY = 800;
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 70, left: 140}}>
      <Rise><H1 size={54}>The Sun never gets more than 1.5° up.</H1></Rise>
      <div style={{height: 12}} />
      <Rise delay={16}><Sub size={30}>So a ridge 100 km away can put you in the dark for a fortnight.</Sub></Rise>
    </div>
    <svg width="1920" height="1080">
      <circle cx={cx} cy={cy} r={Rpx} fill="none" stroke={C.line} strokeWidth="1.5" />
      <circle cx={cx} cy={cy} r={Rpx * 0.62} fill="none" stroke={C.line} strokeWidth="1.5" />
      {Array.from({length: rays}, (_, i) => {
        const a = (2 * Math.PI * i) / 60;
        const len = Rpx * (0.55 + 0.45 * Math.abs(Math.sin(i * 1.7) * 0.6 + Math.sin(i * 0.9) * 0.4));
        return <line key={i} x1={cx} y1={cy} x2={cx + Math.cos(a) * len} y2={cy + Math.sin(a) * len}
          stroke={C.ice} strokeWidth="1.6" opacity="0.5" />;
      })}
      <circle cx={cx} cy={cy} r="7" fill={C.sun} />
      <text x={cx} y={cy + 400} fill={C.dim} fontSize="24" fontFamily={font} textAnchor="middle">
        60 directions, out to 100 km, from every patch of ground
      </text>
      {/* the profile, with the Moon's curvature falling away underneath */}
      <path d={prof.map((v, i) => {
        const x = PX0 + (i / 119) * (PX1 - PX0);
        const curve = drop * 120 * Math.pow(i / 119, 2);
        return `${i ? 'L' : 'M'} ${x} ${PY - v * 42 + curve}`;
      }).join(' ')} fill="none" stroke={C.ink} strokeWidth="2.5" />
      <line x1={PX0} y1={PY} x2={PX1} y2={PY} stroke={C.line} strokeWidth="1.5" strokeDasharray="5 8" />
      <line x1={PX0} y1={PY - 30} x2={PX1} y2={PY - 30} stroke={C.sun} strokeWidth="2" opacity="0.8" />
      <text x={PX0} y={PY - 42} fill={C.sun} fontSize="21" fontFamily={font}>a sunbeam, 1.5° up</text>
      <g opacity={drop}>
        <line x1={PX1} y1={PY} x2={PX1} y2={PY + 120} stroke={C.ice} strokeWidth="2" />
        <text x={PX1 - 14} y={PY + 76} fill={C.ice} fontSize="22" fontFamily={font} textAnchor="end">2.9 km</text>
        <text x={PX1 - 14} y={PY + 104} fill={C.dim} fontSize="20" fontFamily={font} textAnchor="end">of curvature</text>
      </g>
      <text x={PX0} y={PY + 160} fill={C.dim} fontSize="22" fontFamily={font}>
        over 100 km the Moon curves away further than the hills rise
      </text>
    </svg>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 3. the sunlight map
const Sunlight = ({d}) => {
  const f = useCurrentFrame();
  const reveal = interpolate(f, [25, 150], [0, 1], {...clamp, easing: ease});
  const hours = Math.round(interpolate(f, [25, 200], [0, 8766], {...clamp, easing: ease}));
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <MapImage src="sunlight.png" style={{clipPath: `inset(${(1 - reveal) * 100}% 0 0 0)`}} />
    <svg width="1920" height="1080" style={{position: 'absolute'}}><Pole /><Scale /></svg>
    <div style={{position: 'absolute', top: 150, left: 130, width: 520}}>
      <Rise><H1 size={52}>A year of sunlight, one hour at a time.</H1></Rise>
      <div style={{height: 24}} />
      <Rise delay={18}><Sub size={30}>{data.mapped_km2.toLocaleString('en-US')} km² within {data.study_km} km of the pole,
        from NASA's LOLA 40 m elevation map.</Sub></Rise>
      <div style={{height: 46}} />
      <div style={{fontFamily: mono, fontSize: 58, color: C.sun}}>{hours.toLocaleString('en-US')}</div>
      <Sub size={26}>hours of Sun position computed</Sub>
      <div style={{height: 40}} />
      <Sub size={26} color={C.ink}>bright is sunlit · black is never</Sub>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 4. permanent shadow
const Shadow = ({d}) => {
  const f = useCurrentFrame();
  const on = interpolate(f, [40, 110], [0, 1], {...clamp, easing: ease});
  const km2 = Math.round(interpolate(f, [40, 150], [0, data.shadow_km2], clamp));
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <MapImage src="sunlight.png" opacity={0.3 + 0.25 * (1 - on)} />
    <MapImage src="shadow.png" opacity={on} />
    <svg width="1920" height="1080" style={{position: 'absolute'}}><Pole /><Scale /></svg>
    <div style={{position: 'absolute', top: 160, left: 130, width: 540}}>
      <Rise><H1 size={52}>{data.shadow_pct}% of it never sees the Sun.</H1></Rise>
      <div style={{height: 34}} />
      <div style={{fontFamily: font, fontSize: 104, fontWeight: 800, color: C.ice, letterSpacing: -3}}>
        {km2.toLocaleString('en-US')}
      </div>
      <Sub size={28}>km² of permanent shadow · about the size of Puerto Rico</Sub>
      <div style={{height: 40}} />
      <Rise delay={120}><Sub size={30} color={C.ink}>Cold enough that water ice can survive there,
        and it has had billions of years to collect.</Sub></Rise>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 5. the scarcity
const Scarce = ({d}) => {
  const f = useCurrentFrame();
  const rows = data.lit_area;
  const grown = interpolate(f, [30, 170], [0, 1], {...clamp, easing: ease});
  const X0 = 300, X1 = 1500;
  const lx = (km2) => X0 + (Math.log10(Math.max(km2, 0.05)) - Math.log10(0.05)) /
    (Math.log10(300) - Math.log10(0.05)) * (X1 - X0);
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <div style={{position: 'absolute', top: 92, left: 300}}>
      <Rise><H1 size={54}>And sunlight is the thing there is none of.</H1></Rise>
    </div>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      {rows.map((r, i) => {
        const y = 300 + i * 110;
        const w = (lx(r.km2) - X0) * grown;
        return <g key={i}>
          <text x={X0 - 26} y={y + 10} fill={C.dim} fontSize="30" fontFamily={font} textAnchor="end">
            over {r.over_pct}% lit
          </text>
          <rect x={X0} y={y - 24} width={w} height={48} rx="4"
            fill={C.sun} opacity={0.3 + 0.14 * (rows.length - i)} />
          <text x={X0 + w + 22} y={y + 12} fill={C.ink} fontSize="34" fontFamily={mono}
            opacity={grown > 0.9 ? 1 : 0}>{r.km2} km²</text>
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', bottom: 160, left: 300}}>
      <Sub size={23}>bar length is a log scale: each step of the axis is ten times the area</Sub>
    </div>
    <div style={{position: 'absolute', bottom: 70, left: 300, opacity: interpolate(f, [230, 265], [0, 1], clamp)}}>
      <H1 size={40} color={C.sun}>The best single patch on the map: {data.best_lit_pct}% of the year.</H1>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 6. the ratio
const Ratio = ({d}) => {
  const f = useCurrentFrame();
  const n = Math.round(interpolate(f, [20, 120], [0, data.shadow_to_sun_ratio], {...clamp, easing: ease}));
  return <AbsoluteFill style={{opacity: fade(f, d), alignItems: 'center', justifyContent: 'center'}}>
    <Rise><Sub size={34}>shadow to sunlight, by area</Sub></Rise>
    <div style={{height: 18}} />
    <div style={{fontFamily: font, fontSize: 190, fontWeight: 800, color: C.ice, letterSpacing: -8}}>
      {n.toLocaleString('en-US')} : 1
    </div>
    <div style={{height: 36}} />
    <Rise delay={130}><H1 size={46} color={C.sun}>A mission does not have to look for ice.</H1></Rise>
    <div style={{height: 12}} />
    <Rise delay={150}><H1 size={46}>It has to look for somewhere to park.</H1></Rise>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 7. the twelve sites
const Sites = ({d}) => {
  const f = useCurrentFrame();
  const shown = Math.round(interpolate(f, [30, 190], [0, data.sites.length], {...clamp, easing: ease}));
  const rim = interpolate(f, [260, 300], [0, 1], clamp);
  const best = data.sites[0];
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <MapImage src="sunlight.png" opacity={0.95} />
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <Pole label={false} /><Scale />
      <circle cx={sx(0)} cy={sy(0)} r={kmToPx(data.near_pole_km)} fill="none" stroke={C.ice}
        strokeWidth="2" strokeDasharray="6 8" opacity={rim * 0.9} />
      <text x={sx(0)} y={sy(0) - kmToPx(data.near_pole_km) - 12} fill={C.ice} fontSize="20"
        fontFamily={font} textAnchor="middle" opacity={rim}>{data.near_pole_km} km from the pole</text>
      {data.sites.slice(0, shown).map((s, i) =>
        <g key={i}>
          <circle cx={sx(s.x_km)} cy={sy(s.y_km)} r="9" fill="none" stroke={C.moss} strokeWidth="2" />
          <text x={sx(s.x_km) + 13} y={sy(s.y_km) - 8} fill={C.moss} fontSize="20" fontWeight="700"
            fontFamily={font}>{s.rank}</text>
        </g>)}
    </svg>
    <div style={{position: 'absolute', top: 130, left: 130, width: 540}}>
      <Rise><H1 size={52}>The twelve best places to land.</H1></Rise>
      <div style={{height: 20}} />
      <Rise delay={18}><Sub size={28}>Sunlit over half the year, under 10° of slope, with permanent
        shadow within driving range.</Sub></Rise>
      <div style={{height: 40}} />
      <div style={{opacity: interpolate(f, [150, 180], [0, 1], clamp)}}>
        <Sub size={26} color={C.moss}>best site</Sub>
        <div style={{height: 8}} />
        <Sub size={30} color={C.ink}>{best.lat}° · {best.lon}° E</Sub>
        <Sub size={30} color={C.ink}>{best.lit}% sunlit · {best.slope}° slope · {best.ice_km} km to shadow</Sub>
        <Sub size={30} color={C.ink}>{best.relief_m} m above the ground around it</Sub>
      </div>
      <div style={{height: 36}} />
      <div style={{opacity: rim}}>
        <Sub size={28} color={C.ice}>Every one of the twelve stands {(data.relief_min_m / 1000).toFixed(1)} to
          {' '}{(data.relief_max_m / 1000).toFixed(1)} km above the ground around it.
          {' '}{data.near_pole_count} are within {data.near_pole_km} km of the pole, with permanent
          shadow a few kilometres away.</Sub>
      </div>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 8. Earth on the horizon
const EarthView = ({d}) => {
  const f = useCurrentFrame();
  const t = f / 30;
  const bob = Math.sin(t * 1.9);
  const ey = 700 - bob * 115;
  const bars = interpolate(f, [55, 185], [0, 1], {...clamp, easing: ease});
  return <AbsoluteFill style={{opacity: fade(f, d)}}>
    <svg width="1920" height="1080">
      <circle cx={420} cy={ey} r="92" fill={C.ice} opacity="0.07" />
      <circle cx={420} cy={ey} r="46" fill="#1b4f8c" />
      <circle cx={420} cy={ey} r="46" fill="none" stroke={C.ice} strokeWidth="2" />
      <rect x="0" y="770" width="1920" height="310" fill="#15181f" />
      <line x1="0" y1="770" x2="1920" y2="770" stroke={C.dim} strokeWidth="2" opacity="0.5" />
      <text x={420} y={830} fill={C.dim} fontSize="24" fontFamily={font} textAnchor="middle">
        Earth, from the south pole
      </text>
      {data.sites.map((s, i) => {
        const x = 820 + i * 86;
        const h = s.earth * 5.2 * bars;
        return <g key={i}>
          <rect x={x} y={740 - h} width={46} height={h} rx="3" fill={C.ice} opacity="0.75" />
          <text x={x + 23} y={728 - h} fill={C.dim} fontSize="20" fontFamily={mono} textAnchor="middle"
            opacity={bars > 0.95 ? 1 : 0}>{s.earth}</text>
          <text x={x + 23} y={800} fill={C.dim} fontSize="18" fontFamily={font} textAnchor="middle">{s.rank}</text>
        </g>;
      })}
      <line x1={810} y1={740 - 100 * 5.2 * bars} x2={1870} y2={740 - 100 * 5.2 * bars}
        stroke={C.sun} strokeWidth="1.5" strokeDasharray="5 7" opacity={bars} />
      <text x={1870} y={740 - 100 * 5.2 * bars - 12} fill={C.sun} fontSize="20" fontFamily={font}
        textAnchor="end" opacity={bars}>always in view</text>
    </svg>
    <div style={{position: 'absolute', top: 90, left: 130}}>
      <Rise><H1 size={52}>Earth sits down on the horizon.</H1></Rise>
      <div style={{height: 14}} />
      <Rise delay={18}><Sub size={30}>It rises and sets as the Moon's libration tips the pole towards us.</Sub></Rise>
    </div>
    <div style={{position: 'absolute', bottom: 86, left: 130, opacity: interpolate(f, [250, 285], [0, 1], clamp)}}>
      <H1 size={40} color={C.sun}>
        {data.earth_min_pct}% to {data.earth_max_pct}% of the time. Every site needs a relay satellite.
      </H1>
    </div>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- 9. end card
const End = ({d}) => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{opacity: fade(f, d), alignItems: 'center', justifyContent: 'center'}}>
    <Rise><H1 size={74}>Lunar south pole siting</H1></Rise>
    <div style={{height: 22}} />
    <Rise delay={16}><Sub size={34}>Sunlight, shadow and slope from NASA's LOLA elevation map</Sub></Rise>
    <div style={{height: 54}} />
    <Rise delay={30}>
      <div style={{display: 'flex', gap: 86}}>
        {[[data.mapped_km2.toLocaleString('en-US'), 'km² mapped'],
          [data.shadow_km2.toLocaleString('en-US'), 'km² never sunlit'],
          [data.lit_area.find((r) => r.over_pct === 70).km2, 'km² lit over 70%']].map(([v, k], i) =>
          <div key={i} style={{textAlign: 'center'}}>
            <div style={{fontFamily: font, fontSize: 66, fontWeight: 800, color: C.sun, letterSpacing: -2}}>{v}</div>
            <Sub size={24}>{k}</Sub>
          </div>)}
      </div>
    </Rise>
    <div style={{height: 70}} />
    <Rise delay={46}><Sub size={28} color={C.ice}>github.com/cloudynirvana/lunar-south-pole</Sub></Rise>
    <div style={{height: 14}} />
    <Rise delay={54}><Sub size={22}>LOLA LDEM_85S_40M · NASA / Lunar Reconnaissance Orbiter</Sub></Rise>
  </AbsoluteFill>;
};

// ----------------------------------------------------------------
const SCENES = [[Hook, 270], [Skyline, 585], [Sunlight, 390], [Shadow, 420], [Scarce, 435],
                [Ratio, 300], [Sites, 480], [EarthView, 375], [End, 285]];

export const Film = () => {
  let at = 0;
  return <AbsoluteFill style={{background: C.bg}}>
    <Stars />
    <Audio src={staticFile('soundtrack.wav')} />
    {SCENES.map(([Comp, d], i) => {
      const from = at; at += d;
      return <Sequence key={i} from={from} durationInFrames={d}><Comp d={d} /></Sequence>;
    })}
  </AbsoluteFill>;
};
