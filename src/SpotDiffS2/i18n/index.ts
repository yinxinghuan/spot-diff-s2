type Locale = 'zh' | 'en';

const MESSAGES: Record<string, Record<Locale, string>> = {
  'title': { zh: '找茬侦探 II', en: 'SPOT DIFF II' },
  'subtitle': { zh: '和好友一起破解谜团', en: 'Solve mysteries with friends' },
  'startBtn': { zh: '开始调查', en: 'INVESTIGATE' },
  'selectLevel': { zh: '选择案件', en: 'SELECT CASE' },
  'level': { zh: '第 {n} 关', en: 'LEVEL {n}' },
  'locked': { zh: '未解锁', en: 'LOCKED' },
  'found': { zh: '已找到', en: 'FOUND' },
  'time': { zh: '时间', en: 'TIME' },
  'score': { zh: '得分', en: 'SCORE' },
  'errors': { zh: '错误', en: 'ERRORS' },
  'hints': { zh: '提示', en: 'HINTS' },
  'hintBtn': { zh: '提示 ({n})', en: 'HINT ({n})' },
  'noHints': { zh: '无提示', en: 'NO HINTS' },
  'seconds': { zh: '{n}秒', en: '{n}s' },
  'complete': { zh: '案件解决！', en: 'CASE CLOSED!' },
  'allClear': { zh: '全案告破！', en: 'ALL CASES SOLVED!' },
  'allClearSub': { zh: '你是最出色的侦探！', en: 'You are the greatest detective!' },
  'stars': { zh: '{n} 星', en: '{n} Stars' },
  'nextLevel': { zh: '下一关', en: 'NEXT' },
  'replayBtn': { zh: '重玩', en: 'REPLAY' },
  'homeBtn': { zh: '返回', en: 'HOME' },
  'best': { zh: '最高分: {n}', en: 'Best: {n}' },
  'newRecord': { zh: '新纪录！', en: 'NEW RECORD!' },
  'timeBonus': { zh: '时间奖励', en: 'Time Bonus' },
  'errorPenalty': { zh: '错误扣分', en: 'Error Penalty' },
  'hintPenalty': { zh: '提示扣分', en: 'Hint Penalty' },
  'totalScore': { zh: '总分', en: 'Total' },
  'loading': { zh: '加载好友中…', en: 'Loading friends…' },
  'demoMode': { zh: '演示模式', en: 'DEMO MODE' },
};

function detectLocale(): Locale {
  const override = localStorage.getItem('sd2_locale');
  if (override === 'en' || override === 'zh') return override;
  return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

let currentLocale: Locale = detectLocale();

export function getLocale(): Locale {
  return currentLocale;
}

export function t(key: string, vars?: { n?: number | string }): string {
  const entry = MESSAGES[key];
  let str = entry?.[currentLocale] ?? entry?.['en'] ?? key;
  if (vars?.n !== undefined) {
    str = str.replace('{n}', String(vars.n));
  }
  return str;
}

export function useLocale() {
  const setLocale = (l: Locale) => {
    currentLocale = l;
    localStorage.setItem('sd2_locale', l);
  };
  return { t, locale: currentLocale, setLocale };
}
