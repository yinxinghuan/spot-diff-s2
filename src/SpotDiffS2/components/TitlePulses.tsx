import './TitlePulses.less';

interface PulseSlot {
  xPct: number;
  yPct: number;
  delay: number;
  duration: number;
  size: number;
  variant: 'gold' | 'red' | 'reticle';
}

const SLOTS: PulseSlot[] = [
  { xPct: 14, yPct: 16, delay: 0.0, duration: 5.0, size: 38, variant: 'gold' },
  { xPct: 78, yPct: 22, delay: 1.6, duration: 4.4, size: 28, variant: 'gold' },
  { xPct: 24, yPct: 36, delay: 2.8, duration: 5.6, size: 44, variant: 'red' },
  { xPct: 82, yPct: 50, delay: 0.8, duration: 4.8, size: 32, variant: 'gold' },
  { xPct: 16, yPct: 58, delay: 3.4, duration: 5.2, size: 26, variant: 'red' },
  { xPct: 72, yPct: 76, delay: 2.0, duration: 4.6, size: 40, variant: 'gold' },
  { xPct: 28, yPct: 82, delay: 4.2, duration: 5.4, size: 30, variant: 'reticle' },
  { xPct: 60, yPct: 88, delay: 1.0, duration: 4.0, size: 36, variant: 'gold' },
  { xPct: 88, yPct: 38, delay: 3.0, duration: 5.0, size: 22, variant: 'red' },
  { xPct: 8,  yPct: 78, delay: 5.2, duration: 4.8, size: 34, variant: 'gold' },
];

export default function TitlePulses() {
  return (
    <div className="sd-pulses" aria-hidden>
      {SLOTS.map((s, i) => (
        <div
          key={i}
          className={`sd-pulse sd-pulse--${s.variant}`}
          style={{
            left: `${s.xPct}%`,
            top: `${s.yPct}%`,
            // @ts-expect-error CSS custom prop
            '--pulse-size': `${s.size}px`,
            animationDelay: `${s.delay}s`,
            animationDuration: `${s.duration}s`,
          }}
        />
      ))}
    </div>
  );
}
