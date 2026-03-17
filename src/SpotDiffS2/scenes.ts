import type { SceneDef } from './types';

import occultBase from './img/levels/occult/base.png';
import occultDiff from './img/levels/occult/diff.png';
import commandBase from './img/levels/command/base.png';
import commandDiff from './img/levels/command/diff.png';
import loungeBase from './img/levels/lounge/base.png';
import loungeDiff from './img/levels/lounge/diff.png';
import manorBase from './img/levels/manor/base.png';
import manorDiff from './img/levels/manor/diff.png';
import templeBase from './img/levels/temple/base.png';
import templeDiff from './img/levels/temple/diff.png';
import gymBase from './img/levels/gym/base.png';
import gymDiff from './img/levels/gym/diff.png';

export const SCENES: SceneDef[] = [
  {
    id: 'occult',
    baseImg: occultBase,
    diffImg: occultDiff,
    differences: [
      { id: 'occult_1', cx: 0.497, cy: 0.550, r: 0.08, label_zh: '沙漏', label_en: 'Hourglass', emoji: '⏳' },
      { id: 'occult_2', cx: 0.376, cy: 0.545, r: 0.08, label_zh: '蛇', label_en: 'Snake', emoji: '🐍' },
      { id: 'occult_3', cx: 0.322, cy: 0.442, r: 0.08, label_zh: '魔法书', label_en: 'Spellbook', emoji: '📖' },
    ],
  },
  {
    id: 'command',
    baseImg: commandBase,
    diffImg: commandDiff,
    differences: [
      { id: 'cmd_1', cx: 0.818, cy: 0.261, r: 0.08, label_zh: '宝剑', label_en: 'Sword', emoji: '⚔️' },
      { id: 'cmd_2', cx: 0.736, cy: 0.937, r: 0.08, label_zh: '密函', label_en: 'Dispatch', emoji: '📜' },
      { id: 'cmd_3', cx: 0.275, cy: 0.609, r: 0.08, label_zh: '望远镜', label_en: 'Binoculars', emoji: '🔭' },
    ],
  },
  {
    id: 'lounge',
    baseImg: loungeBase,
    diffImg: loungeDiff,
    differences: [
      { id: 'lounge_1', cx: 0.149, cy: 0.732, r: 0.08, label_zh: '比萨盒', label_en: 'Pizza box', emoji: '🍕' },
      { id: 'lounge_2', cx: 0.732, cy: 0.160, r: 0.08, label_zh: '抱枕', label_en: 'Cushion', emoji: '🛋️' },
      { id: 'lounge_3', cx: 0.643, cy: 0.159, r: 0.08, label_zh: '仙人掌', label_en: 'Cactus', emoji: '🌵' },
    ],
  },
  {
    id: 'manor',
    baseImg: manorBase,
    diffImg: manorDiff,
    differences: [
      { id: 'manor_1', cx: 0.310, cy: 0.204, r: 0.13, label_zh: '猫咪', label_en: 'Cat', emoji: '🐱' },
      { id: 'manor_2', cx: 0.766, cy: 0.622, r: 0.08, label_zh: '蜡烛台', label_en: 'Candelabra', emoji: '🕯️' },
      { id: 'manor_3', cx: 0.216, cy: 0.124, r: 0.08, label_zh: '书', label_en: 'Book', emoji: '📚' },
    ],
  },
  {
    id: 'temple',
    baseImg: templeBase,
    diffImg: templeDiff,
    differences: [
      { id: 'temple_1', cx: 0.389, cy: 0.347, r: 0.12, label_zh: '水晶球', label_en: 'Crystal orb', emoji: '🔮' },
      { id: 'temple_2', cx: 0.607, cy: 0.531, r: 0.11, label_zh: '佛像', label_en: 'Buddha statue', emoji: '🪬' },
      { id: 'temple_3', cx: 0.874, cy: 0.713, r: 0.08, label_zh: '古卷', label_en: 'Ancient scroll', emoji: '📜' },
    ],
  },
  {
    id: 'gym',
    baseImg: gymBase,
    diffImg: gymDiff,
    differences: [
      { id: 'gym_1', cx: 0.914, cy: 0.825, r: 0.08, label_zh: '毛巾', label_en: 'Towel', emoji: '🏋️' },
      { id: 'gym_2', cx: 0.443, cy: 0.436, r: 0.08, label_zh: '擂台绳', label_en: 'Ring ropes', emoji: '🥊' },
      { id: 'gym_3', cx: 0.224, cy: 0.388, r: 0.08, label_zh: '水瓶', label_en: 'Water bottle', emoji: '💧' },
    ],
  },
];
