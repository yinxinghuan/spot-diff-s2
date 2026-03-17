/** Design field: 390×680 portrait */
export const FIELD_W = 390;
export const FIELD_H = 680;

export interface DiffRegion {
  id: string;
  /** Normalized center X (0-1) */
  cx: number;
  /** Normalized center Y (0-1) */
  cy: number;
  /** Normalized hit radius */
  r: number;
  label_zh: string;
  label_en: string;
  emoji: string;
}

/** Static scene data — images & differences, no character info */
export interface SceneDef {
  /** Scene id, e.g. 'occult', 'command' */
  id: string;
  baseImg: string;
  diffImg: string;
  differences: DiffRegion[];
  /** Local character illustration (transparent PNG, portrait ratio) */
  charImg: string;
  /** Detective-style card portrait (512×512) for level select */
  cardImg: string;
}

/** A contact fetched from Aigram API */
export interface AigramContact {
  telegram_id: string;
  name: string;
  /** Remote URL of the user's avatar */
  head_url: string;
}

/** A full playable level = SceneDef + character from API */
export interface LevelDef extends SceneDef {
  charName: string;
  /** Remote URL — used directly as <img src> */
  avatarUrl: string;
  /** Aigram telegram_id — used for AW.PROFILE.OPEN */
  telegramId: string;
}

export type GamePhase = 'loading' | 'idle' | 'select' | 'playing' | 'complete' | 'allClear';

export interface LevelResult {
  stars: number;
  score: number;
  time: number;
  errors: number;
  hints: number;
}

export interface SaveData {
  /** Unlocked level count (1-based, first level always unlocked) */
  unlocked: number;
  /** Best result per level id */
  results: Record<string, LevelResult>;
}
