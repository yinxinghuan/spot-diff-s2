import { useState, useRef, useCallback, useEffect } from 'react';
import type { GamePhase, LevelDef, LevelResult, SaveData } from '../types';
import { SCENES } from '../scenes';
import { getLocale } from '../i18n';
import { useAigramContacts } from './useAigramContacts';
import { resumeAudio, playTap, playFound, playWrong, playHint, playComplete, playStart } from '../utils/sounds';

const STORAGE_KEY = 'sd2_save';
const POINTS_PER_FIND = 100;
const TIME_BONUS_MAX = 300;
const TIME_PENALTY_RATE = 2;
const ERROR_PENALTY = 15;
const HINT_PENALTY = 30;
const STAR3_THRESHOLD = 0.8;
const STAR2_THRESHOLD = 0.5;
const MAX_HINTS = 3;
const COOLDOWN_MS = 500;

function loadSave(): SaveData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* ignore */ }
  return { unlocked: 1, results: {} };
}

function writeSave(data: SaveData) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function calcScore(found: number, time: number, errors: number, hints: number): number {
  const findScore = found * POINTS_PER_FIND;
  const timeBonus = Math.max(0, TIME_BONUS_MAX - time * TIME_PENALTY_RATE);
  const errorPen = errors * ERROR_PENALTY;
  const hintPen = hints * HINT_PENALTY;
  return Math.max(0, findScore + timeBonus - errorPen - hintPen);
}

function calcStars(score: number, totalDiffs: number): number {
  const maxScore = totalDiffs * POINTS_PER_FIND + TIME_BONUS_MAX;
  const ratio = score / maxScore;
  if (ratio >= STAR3_THRESHOLD) return 3;
  if (ratio >= STAR2_THRESHOLD) return 2;
  return 1;
}

/** Scene-themed bubble dialogue — each scene id maps to lines */
const SCENE_DIALOGUE: Record<string, {
  start: { zh: string; en: string };
  found: { zh: string; en: string };
  wrong: { zh: string; en: string };
  clear: { zh: string; en: string };
}> = {
  cafe: {
    start: { zh: '这家咖啡馆有什么不一样？', en: 'Something in this café looks off…' },
    found: { zh: '对！就是这个！', en: 'Yes! That\'s the one!' },
    wrong: { zh: '这里看起来一样哦~', en: 'Nothing different here~' },
    clear: { zh: '全找到了！来杯咖啡庆祝！', en: 'All found! Coffee break!' },
  },
  vinyl: {
    start: { zh: '这家唱片店有人动过东西…', en: 'Something\'s been moved in this record store…' },
    found: { zh: '好眼力！', en: 'Sharp eyes!' },
    wrong: { zh: '不是这里…再找找', en: 'Not here… keep looking' },
    clear: { zh: '完美！像侦探一样！', en: 'Perfect! Just like a detective!' },
  },
  bar: {
    start: { zh: '这个吧台有点奇怪…', en: 'Something\'s off behind this bar…' },
    found: { zh: '发现了！干杯！', en: 'Found it! Cheers!' },
    wrong: { zh: '唔，不对啊', en: 'Hmm, that\'s not it' },
    clear: { zh: '全破解了！最后一轮！', en: 'All solved! One more round!' },
  },
  library: {
    start: { zh: '有人动了这里的书架…', en: 'Someone rearranged this library…' },
    found: { zh: '翻到正确答案了！', en: 'Found the right answer!' },
    wrong: { zh: '这页没有不同', en: 'No difference on this page' },
    clear: { zh: '全部解开！博学侦探！', en: 'All done! Brilliant detective!' },
  },
  kitchen: {
    start: { zh: '这厨房好像有点不一样？', en: 'This kitchen looks a bit different…' },
    found: { zh: '嗯，发现了！', en: 'Found it!' },
    wrong: { zh: '这里没变化~', en: 'No change here~' },
    clear: { zh: '全找到了！完美配方！', en: 'All found! Perfect recipe!' },
  },
  rooftop: {
    start: { zh: '这个屋顶有什么变化？', en: 'Something changed on this rooftop…' },
    found: { zh: '找到了！城市的眼睛！', en: 'Found it! Eyes of the city!' },
    wrong: { zh: '夜色迷人但不是这里', en: 'Beautiful night, but not here' },
    clear: { zh: '全破案！星光见证你！', en: 'Case closed! Stars witness it all!' },
  },
};

function getSceneDialogue(sceneId: string, type: 'start' | 'found' | 'wrong' | 'clear'): string {
  const isZh = getLocale() === 'zh';
  const scene = SCENE_DIALOGUE[sceneId] ?? SCENE_DIALOGUE['cafe'];
  const line = scene[type];
  return isZh ? line.zh : line.en;
}

export type BubbleMood = 'normal' | 'happy';

export function useSpotDiffS2() {
  const { contacts, loading: contactsLoading } = useAigramContacts();

  // Build levels by merging scenes + contacts
  const levels: LevelDef[] = SCENES.map((scene, idx) => {
    const contact = contacts[idx];
    return {
      ...scene,
      charName: contact?.name ?? `Player ${idx + 1}`,
      avatarUrl: contact?.head_url ?? '',
    };
  });

  const [phase, setPhase] = useState<GamePhase>('loading');
  const [save, setSave] = useState<SaveData>(loadSave);
  const [currentLevel, setCurrentLevel] = useState<LevelDef | null>(null);
  const [foundIds, setFoundIds] = useState<Set<string>>(new Set());
  const [time, setTime] = useState(0);
  const [errors, setErrors] = useState(0);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [lastResult, setLastResult] = useState<LevelResult | null>(null);
  const [isNewRecord, setIsNewRecord] = useState(false);
  const [bubbleText, setBubbleText] = useState<string | null>(null);
  const [bubbleMood, setBubbleMood] = useState<BubbleMood>('normal');
  const [bubbleLeaving, setBubbleLeaving] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const [hintTarget, setHintTarget] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const bubbleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bubbleLeaveRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const vagueHintShownRef = useRef<Set<string>>(new Set());

  // Transition from loading → idle once contacts are ready
  useEffect(() => {
    if (!contactsLoading && phase === 'loading') {
      setPhase('idle');
    }
  }, [contactsLoading, phase]);

  // Timer
  useEffect(() => {
    if (phase === 'playing') {
      timerRef.current = setInterval(() => setTime(t => t + 1), 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  const showBubble = useCallback((text: string, durationMs = 1500, mood: BubbleMood = 'normal') => {
    if (bubbleTimerRef.current) clearTimeout(bubbleTimerRef.current);
    if (bubbleLeaveRef.current) clearTimeout(bubbleLeaveRef.current);
    setBubbleLeaving(false);
    setBubbleMood(mood);
    setBubbleText(text);
    bubbleTimerRef.current = setTimeout(() => {
      setBubbleLeaving(true);
      bubbleLeaveRef.current = setTimeout(() => {
        setBubbleText(null);
        setBubbleLeaving(false);
      }, 300);
    }, durationMs);
  }, []);

  const goToSelect = useCallback(() => {
    setPhase('select');
    setCurrentLevel(null);
    setLastResult(null);
  }, []);

  const goHome = useCallback(() => {
    setPhase('idle');
    setCurrentLevel(null);
    setLastResult(null);
  }, []);

  const startLevel = useCallback((levelId: string) => {
    const level = levels.find(l => l.id === levelId);
    if (!level) return;
    setCurrentLevel(level);
    setFoundIds(new Set());
    setTime(0);
    setErrors(0);
    setHintsUsed(0);
    setLastResult(null);
    setIsNewRecord(false);
    setHintTarget(null);
    setBubbleText(null);
    vagueHintShownRef.current = new Set();
    setPhase('playing');
    resumeAudio();
    playStart();
    setTimeout(() => {
      showBubble(getSceneDialogue(level.id, 'start'), 2000, 'normal');
    }, 500);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [levels, showBubble]);

  const completeLevel = useCallback((level: LevelDef, finalTime: number, finalErrors: number, finalHints: number) => {
    if (timerRef.current) clearInterval(timerRef.current);

    const score = calcScore(level.differences.length, finalTime, finalErrors, finalHints);
    const stars = calcStars(score, level.differences.length);
    const result: LevelResult = { stars, score, time: finalTime, errors: finalErrors, hints: finalHints };
    setLastResult(result);

    const newSave = { ...save };
    const prev = newSave.results[level.id];
    const isRecord = !prev || score > prev.score;
    if (isRecord) {
      newSave.results[level.id] = result;
    }

    const levelIdx = levels.findIndex(l => l.id === level.id);
    if (levelIdx + 2 > newSave.unlocked) {
      newSave.unlocked = Math.min(levelIdx + 2, levels.length);
    }

    writeSave(newSave);
    setSave(newSave);
    setIsNewRecord(isRecord);
    setPhase('complete');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [save, levels]);

  const handleTap = useCallback((nx: number, ny: number) => {
    if (phase !== 'playing' || !currentLevel || cooldown) return;
    playTap();

    for (const diff of currentLevel.differences) {
      if (foundIds.has(diff.id)) continue;
      const dx = nx - diff.cx;
      const dy = ny - diff.cy;
      if (Math.sqrt(dx * dx + dy * dy) <= diff.r) {
        const newFound = new Set(foundIds);
        newFound.add(diff.id);
        setFoundIds(newFound);
        setHintTarget(null);
        playFound();
        showBubble(getSceneDialogue(currentLevel.id, 'found'), 1500, 'happy');

        if (newFound.size === currentLevel.differences.length) {
          playComplete();
          showBubble(getSceneDialogue(currentLevel.id, 'clear'), 2500, 'happy');
          setTimeout(() => {
            completeLevel(currentLevel, time, errors, hintsUsed);
          }, 2000);
        }
        return;
      }
    }

    playWrong();
    setErrors(e => e + 1);
    setCooldown(true);
    showBubble(getSceneDialogue(currentLevel.id, 'wrong'), 1500, 'normal');
    setTimeout(() => setCooldown(false), COOLDOWN_MS);
  }, [phase, currentLevel, cooldown, foundIds, time, errors, hintsUsed, completeLevel, showBubble]);

  const useHint = useCallback(() => {
    if (phase !== 'playing' || !currentLevel || hintsUsed >= MAX_HINTS) return;

    const remaining = currentLevel.differences.filter(d => !foundIds.has(d.id));
    if (remaining.length === 0) return;

    const target = remaining[Math.floor(Math.random() * remaining.length)];
    setHintsUsed(h => h + 1);
    setHintTarget(null);
    playHint();

    const isZh = getLocale() === 'zh';
    const label = isZh ? target.label_zh : target.label_en;

    if (!vagueHintShownRef.current.has(target.id)) {
      vagueHintShownRef.current.add(target.id);
      const area = target.cy < 0.33 ? (isZh ? '上方' : 'upper area')
        : target.cy > 0.66 ? (isZh ? '下方' : 'lower area')
        : (isZh ? '中间' : 'middle area');
      const side = target.cx < 0.33 ? (isZh ? '左侧' : 'left side')
        : target.cx > 0.66 ? (isZh ? '右侧' : 'right side')
        : (isZh ? '中央' : 'center');
      const vagueMsg = isZh ? `试试看${area}${side}…` : `Try the ${area}, ${side}...`;
      showBubble(vagueMsg, 2500);
    } else {
      const specificMsg = isZh ? `注意看${label}！` : `Look at the ${label}!`;
      showBubble(specificMsg, 2500);
    }
    // Show hint marker after a brief delay
    setTimeout(() => setHintTarget(target.id), 300);
  }, [phase, currentLevel, hintsUsed, foundIds, showBubble]);

  const nextLevel = useCallback(() => {
    if (!currentLevel) return;
    const idx = levels.findIndex(l => l.id === currentLevel.id);
    if (idx < levels.length - 1) {
      startLevel(levels[idx + 1].id);
    } else {
      setPhase('allClear');
    }
  }, [currentLevel, levels, startLevel]);

  return {
    phase,
    save,
    currentLevel,
    foundIds,
    time,
    errors,
    hintsUsed,
    maxHints: MAX_HINTS,
    lastResult,
    isNewRecord,
    bubbleText,
    bubbleMood,
    bubbleLeaving,
    cooldown,
    hintTarget,
    levels,
    contactsLoading,
    goHome,
    goToSelect,
    startLevel,
    handleTap,
    useHint,
    nextLevel,
  };
}
