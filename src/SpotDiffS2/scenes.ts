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

/**
 * 6 static scenes for Season 2.
 * Differences coordinates are normalized (0-1) and will be updated
 * after images are generated and analyzed via find_diffs.py.
 */
export const SCENES: SceneDef[] = [
  {
    id: 'cafe',
    baseImg: cafeBase,
    diffImg: cafeDiff,
    differences: [
      // TODO: fill in after image generation
      { id: 'cafe_1', cx: 0.25, cy: 0.3, r: 0.12, label_zh: '咖啡杯', label_en: 'Coffee cup', emoji: '☕' },
      { id: 'cafe_2', cx: 0.7, cy: 0.55, r: 0.12, label_zh: '糕点', label_en: 'Pastry', emoji: '🥐' },
      { id: 'cafe_3', cx: 0.5, cy: 0.8, r: 0.10, label_zh: '盆栽', label_en: 'Plant', emoji: '🌿' },
    ],
  },
  {
    id: 'vinyl',
    baseImg: vinylBase,
    diffImg: vinylDiff,
    differences: [
      { id: 'vinyl_1', cx: 0.2, cy: 0.4, r: 0.12, label_zh: '黑胶唱片', label_en: 'Vinyl record', emoji: '💿' },
      { id: 'vinyl_2', cx: 0.65, cy: 0.25, r: 0.12, label_zh: '霓虹招牌', label_en: 'Neon sign', emoji: '🎵' },
      { id: 'vinyl_3', cx: 0.4, cy: 0.75, r: 0.10, label_zh: '磁带', label_en: 'Cassette', emoji: '📼' },
    ],
  },
  {
    id: 'bar',
    baseImg: barBase,
    diffImg: barDiff,
    differences: [
      { id: 'bar_1', cx: 0.3, cy: 0.35, r: 0.12, label_zh: '酒瓶', label_en: 'Bottle', emoji: '🍾' },
      { id: 'bar_2', cx: 0.72, cy: 0.6, r: 0.12, label_zh: '鸡尾酒', label_en: 'Cocktail', emoji: '🍸' },
      { id: 'bar_3', cx: 0.5, cy: 0.85, r: 0.10, label_zh: '吧凳', label_en: 'Bar stool', emoji: '🪑' },
    ],
  },
  {
    id: 'library',
    baseImg: libraryBase,
    diffImg: libraryDiff,
    differences: [
      { id: 'lib_1', cx: 0.2, cy: 0.3, r: 0.12, label_zh: '书本', label_en: 'Book', emoji: '📚' },
      { id: 'lib_2', cx: 0.75, cy: 0.5, r: 0.12, label_zh: '地球仪', label_en: 'Globe', emoji: '🌍' },
      { id: 'lib_3', cx: 0.45, cy: 0.8, r: 0.10, label_zh: '蜡烛', label_en: 'Candle', emoji: '🕯️' },
    ],
  },
  {
    id: 'kitchen',
    baseImg: kitchenBase,
    diffImg: kitchenDiff,
    differences: [
      { id: 'kitch_1', cx: 0.3, cy: 0.4, r: 0.12, label_zh: '水果碗', label_en: 'Fruit bowl', emoji: '🍎' },
      { id: 'kitch_2', cx: 0.68, cy: 0.3, r: 0.12, label_zh: '香料瓶', label_en: 'Spice jar', emoji: '🧂' },
      { id: 'kitch_3', cx: 0.5, cy: 0.75, r: 0.10, label_zh: '窗台植物', label_en: 'Window plant', emoji: '🌱' },
    ],
  },
  {
    id: 'rooftop',
    baseImg: rooftopBase,
    diffImg: rooftopDiff,
    differences: [
      { id: 'roof_1', cx: 0.25, cy: 0.35, r: 0.12, label_zh: '城市灯光', label_en: 'City lights', emoji: '🌃' },
      { id: 'roof_2', cx: 0.7, cy: 0.5, r: 0.12, label_zh: '望远镜', label_en: 'Telescope', emoji: '🔭' },
      { id: 'roof_3', cx: 0.5, cy: 0.8, r: 0.10, label_zh: '花盆', label_en: 'Flower pot', emoji: '🌸' },
    ],
  },
];
