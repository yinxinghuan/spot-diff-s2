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
  occult: {
    start: { zh: '这暗室里有什么被动过？', en: 'Something moved in this dark den...' },
    found: { zh: '呵，这个骗不了我。', en: 'Heh, can\'t fool me.' },
    wrong: { zh: '不是这里，凡人。', en: 'Not there, mortal.' },
    clear: { zh: '全找到了！献给黑暗！', en: 'All found! For the darkness!' },
  },
  command: {
    start: { zh: '情报显示这里有异常…', en: 'Intel says something\'s off here...' },
    found: { zh: '报告确认！', en: 'Target confirmed!' },
    wrong: { zh: '重新侦察，士兵。', en: 'Scout again, soldier.' },
    clear: { zh: '任务完成！全员撤退！', en: 'Mission complete! Fall back!' },
  },
  lounge: {
    start: { zh: '好像…有什么不一样？算了先看看', en: 'Hmm... something\'s different? Whatever, let\'s check' },
    found: { zh: '哦。对哦。', en: 'Oh. Yeah.' },
    wrong: { zh: '不是这个……再说了也无所谓', en: 'Not this... whatever' },
    clear: { zh: '找完了。继续躺着。', en: 'Done. Back to chilling.' },
  },
  manor: {
    start: { zh: '这厅堂有些不妥，请协助排查。', en: 'Something is amiss in this hall, assist me.' },
    found: { zh: '好眼力，孺子可教。', en: 'Good eye, well done.' },
    wrong: { zh: '此处无异，请再仔细些。', en: 'Nothing here, look more carefully.' },
    clear: { zh: '全部找出，干杯！', en: 'All found, I propose a toast!' },
  },
  temple: {
    start: { zh: '此间有扰动…静心感受。', en: 'A disturbance here... clear your mind.' },
    found: { zh: '善。你已触碰真相。', en: 'Good. You have touched the truth.' },
    wrong: { zh: '非也。再观察。', en: 'No. Look again.' },
    clear: { zh: '全数破解。开悟之路已近。', en: 'All revealed. Enlightenment approaches.' },
  },
  gym: {
    start: { zh: '这拳馆有什么变了！冲！', en: 'Something changed in the gym! Let\'s go!' },
    found: { zh: '打中了！', en: 'Hit it!' },
    wrong: { zh: '出拳失误，再来！', en: 'Missed! Try again!' },
    clear: { zh: '全中！冠军的眼睛！', en: 'All hits! Champion eyes!' },
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
      telegramId: contact?.telegram_id ?? '',
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
