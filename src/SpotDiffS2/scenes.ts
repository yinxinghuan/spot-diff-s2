import type { SceneDef } from './types';

import cafeBase from './img/levels/cafe/base.png';
import cafeDiff from './img/levels/cafe/diff.png';
import vinylBase from './img/levels/vinyl/base.png';
import vinylDiff from './img/levels/vinyl/diff.png';
import barBase from './img/levels/bar/base.png';
import barDiff from './img/levels/bar/diff.png';
import libraryBase from './img/levels/library/base.png';
import libraryDiff from './img/levels/library/diff.png';
import kitchenBase from './img/levels/kitchen/base.png';
import kitchenDiff from './img/levels/kitchen/diff.png';
import rooftopBase from './img/levels/rooftop/base.png';
import rooftopDiff from './img/levels/rooftop/diff.png';

export const SCENES: SceneDef[] = [
  {
    id: 'cafe',
    baseImg: cafeBase,
    diffImg: cafeDiff,
    differences: [
      { id: 'cafe_1', cx: 0.748, cy: 0.855, r: 0.09, label_zh: '记事本', label_en: 'Notebook', emoji: '📓' },
      { id: 'cafe_2', cx: 0.797, cy: 0.668, r: 0.08, label_zh: '咖啡研磨机', label_en: 'Coffee grinder', emoji: '☕' },
      { id: 'cafe_3', cx: 0.039, cy: 0.537, r: 0.08, label_zh: '多肉植物', label_en: 'Succulent', emoji: '🌵' },
    ],
  },
  {
    id: 'vinyl',
    baseImg: vinylBase,
    diffImg: vinylDiff,
    differences: [
      { id: 'vinyl_1', cx: 0.271, cy: 0.255, r: 0.16, label_zh: '霓虹招牌', label_en: 'Neon sign', emoji: '🎵' },
      { id: 'vinyl_2', cx: 0.464, cy: 0.043, r: 0.09, label_zh: '海报', label_en: 'Poster', emoji: '🎸' },
      { id: 'vinyl_3', cx: 0.570, cy: 0.015, r: 0.08, label_zh: '顶部装饰', label_en: 'Top decor', emoji: '🎶' },
    ],
  },
  {
    id: 'bar',
    baseImg: barBase,
    diffImg: barDiff,
    differences: [
      { id: 'bar_1', cx: 0.680, cy: 0.079, r: 0.11, label_zh: '霓虹灯牌', label_en: 'Neon sign', emoji: '🍸' },
      { id: 'bar_2', cx: 0.703, cy: 0.262, r: 0.08, label_zh: '酒架物品', label_en: 'Shelf item', emoji: '🍾' },
      { id: 'bar_3', cx: 0.354, cy: 0.235, r: 0.08, label_zh: '装饰细节', label_en: 'Bar detail', emoji: '🍋' },
    ],
  },
  {
    id: 'library',
    baseImg: libraryBase,
    diffImg: libraryDiff,
    differences: [
      { id: 'lib_1', cx: 0.858, cy: 0.378, r: 0.08, label_zh: '望远镜', label_en: 'Telescope', emoji: '🔭' },
      { id: 'lib_2', cx: 0.845, cy: 0.112, r: 0.08, label_zh: '相框', label_en: 'Picture frame', emoji: '🖼️' },
      { id: 'lib_3', cx: 0.836, cy: 0.269, r: 0.08, label_zh: '书架装饰', label_en: 'Shelf decor', emoji: '📚' },
    ],
  },
  {
    id: 'kitchen',
    baseImg: kitchenBase,
    diffImg: kitchenDiff,
    differences: [
      { id: 'kitch_1', cx: 0.145, cy: 0.786, r: 0.12, label_zh: '茶巾', label_en: 'Tea towel', emoji: '🧺' },
      { id: 'kitch_2', cx: 0.262, cy: 0.452, r: 0.08, label_zh: '水果碗', label_en: 'Fruit bowl', emoji: '🍇' },
      { id: 'kitch_3', cx: 0.298, cy: 0.890, r: 0.08, label_zh: '窗台植物', label_en: 'Window plant', emoji: '🌿' },
    ],
  },
  {
    id: 'rooftop',
    baseImg: rooftopBase,
    diffImg: rooftopDiff,
    differences: [
      { id: 'roof_1', cx: 0.328, cy: 0.506, r: 0.08, label_zh: '花盆', label_en: 'Flower pot', emoji: '🌸' },
      { id: 'roof_2', cx: 0.936, cy: 0.235, r: 0.08, label_zh: '灯笼', label_en: 'Lantern', emoji: '🏮' },
      { id: 'roof_3', cx: 0.809, cy: 0.305, r: 0.08, label_zh: '装饰灯', label_en: 'Fairy lights', emoji: '✨' },
    ],
  },
];
