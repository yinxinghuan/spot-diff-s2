/**
 * Spot-Diff sound effects — Web Audio API, no audio files needed.
 * Detective/noir theme: muted tones, subtle clicks, satisfying chimes.
 */

let audioCtx: AudioContext | null = null;
const getCtx = (): AudioContext => {
  if (!audioCtx) audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  return audioCtx;
};

export const resumeAudio = (): void => {
  const ctx = getCtx();
  if (ctx.state === 'suspended') ctx.resume();
};

function tone(
  freq: number,
  duration: number,
  opts: {
    type?: OscillatorType;
    gain?: number;
    freqEnd?: number;
    gainEnd?: number;
    delay?: number;
  } = {}
) {
  try {
    const ctx = getCtx();
    const now = ctx.currentTime + (opts.delay || 0);
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = opts.type || 'sine';
    osc.frequency.setValueAtTime(freq, now);
    if (opts.freqEnd) osc.frequency.exponentialRampToValueAtTime(opts.freqEnd, now + duration);
    g.gain.setValueAtTime(opts.gain ?? 0.08, now);
    g.gain.exponentialRampToValueAtTime(opts.gainEnd ?? 0.001, now + duration);
    osc.connect(g).connect(ctx.destination);
    osc.start(now);
    osc.stop(now + duration);
  } catch { /* ignore */ }
}

/** Tap/click on image */
export function playTap(): void {
  tone(400, 0.06, { type: 'sine', gain: 0.06, freqEnd: 300 });
}

/** Found a difference — satisfying discovery chime */
export function playFound(): void {
  tone(523, 0.15, { type: 'triangle', gain: 0.1 });
  tone(659, 0.15, { type: 'triangle', gain: 0.1, delay: 0.08 });
  tone(784, 0.2, { type: 'triangle', gain: 0.08, delay: 0.16 });
}

/** Wrong tap — dull buzz */
export function playWrong(): void {
  tone(180, 0.15, { type: 'square', gain: 0.05, freqEnd: 120 });
}

/** Hint used — subtle notification */
export function playHint(): void {
  tone(880, 0.1, { type: 'sine', gain: 0.06, freqEnd: 660 });
}

/** Level complete — victory fanfare */
export function playComplete(): void {
  tone(523, 0.15, { type: 'triangle', gain: 0.1 });
  tone(659, 0.15, { type: 'triangle', gain: 0.1, delay: 0.12 });
  tone(784, 0.15, { type: 'triangle', gain: 0.1, delay: 0.24 });
  tone(1047, 0.3, { type: 'triangle', gain: 0.12, delay: 0.36 });
}

/** Button click */
export function playClick(): void {
  tone(600, 0.04, { type: 'sine', gain: 0.05, freqEnd: 400 });
}

/** Level start */
export function playStart(): void {
  tone(330, 0.12, { type: 'triangle', gain: 0.07 });
  tone(440, 0.12, { type: 'triangle', gain: 0.07, delay: 0.1 });
}
