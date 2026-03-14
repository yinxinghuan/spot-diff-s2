import type { LevelDef } from '../types';

import algramBase from '../img/levels/algram/base.png';
import jennyBase from '../img/levels/jenny/base.png';
import jmfBase from '../img/levels/jmf/base.png';
import ghostpixelBase from '../img/levels/ghostpixel/base.png';
import isayaBase from '../img/levels/isaya/base.png';
import isabelBase from '../img/levels/isabel/base.png';

import algramDiff from '../img/levels/algram/diff.png';
import jennyDiff from '../img/levels/jenny/diff.png';
import jmfDiff from '../img/levels/jmf/diff.png';
import ghostpixelDiff from '../img/levels/ghostpixel/diff.png';
import isayaDiff from '../img/levels/isaya/diff.png';
import isabelDiff from '../img/levels/isabel/diff.png';

export const LEVELS: LevelDef[] = [
  {
    id: 'algram',
    charId: 'algram',
    charName: 'Algram',
    baseImg: algramBase,
    diffImg: algramDiff,
    differences: [
      { id: 'a1', cx: 0.10, cy: 0.55, r: 0.07, label_zh: '吉他颜色', label_en: 'Guitar color' },
      { id: 'a2', cx: 0.22, cy: 0.78, r: 0.07, label_zh: '耳机', label_en: 'Headphones' },
      { id: 'a3', cx: 0.30, cy: 0.07, r: 0.07, label_zh: '墙上海报', label_en: 'Wall poster' },
      { id: 'a4', cx: 0.55, cy: 0.07, r: 0.07, label_zh: '海报图案', label_en: 'Poster design' },
      { id: 'a5', cx: 0.38, cy: 0.87, r: 0.07, label_zh: '踏板颜色', label_en: 'Pedal color' },
    ],
  },
  {
    id: 'jenny',
    charId: 'jenny',
    charName: 'Jenny',
    baseImg: jennyBase,
    diffImg: jennyDiff,
    differences: [
      { id: 'j1', cx: 0.10, cy: 0.42, r: 0.07, label_zh: '台灯颜色', label_en: 'Lamp color' },
      { id: 'j2', cx: 0.78, cy: 0.55, r: 0.07, label_zh: '猫咪颜色', label_en: 'Cat color' },
      { id: 'j3', cx: 0.35, cy: 0.72, r: 0.07, label_zh: '咖啡杯', label_en: 'Coffee mug' },
      { id: 'j4', cx: 0.33, cy: 0.13, r: 0.07, label_zh: '便签颜色', label_en: 'Sticky notes' },
      { id: 'j5', cx: 0.08, cy: 0.72, r: 0.07, label_zh: '书本植物', label_en: 'Books & plant' },
    ],
  },
  {
    id: 'jmf',
    charId: 'jmf',
    charName: 'JM·F',
    baseImg: jmfBase,
    diffImg: jmfDiff,
    differences: [
      { id: 'm1', cx: 0.50, cy: 0.06, r: 0.08, label_zh: '霓虹灯颜色', label_en: 'Neon light' },
      { id: 'm2', cx: 0.75, cy: 0.40, r: 0.07, label_zh: '服务器LED', label_en: 'Server LED' },
      { id: 'm3', cx: 0.45, cy: 0.80, r: 0.07, label_zh: '地面线缆', label_en: 'Floor cables' },
      { id: 'm4', cx: 0.88, cy: 0.65, r: 0.07, label_zh: '椅子颜色', label_en: 'Chair color' },
      { id: 'm5', cx: 0.18, cy: 0.35, r: 0.07, label_zh: '屏幕文字', label_en: 'Screen text' },
    ],
  },
  {
    id: 'ghostpixel',
    charId: 'ghostpixel',
    charName: 'ghostpixel',
    baseImg: ghostpixelBase,
    diffImg: ghostpixelDiff,
    differences: [
      { id: 'g1', cx: 0.50, cy: 0.45, r: 0.08, label_zh: '传送门颜色', label_en: 'Portal color' },
      { id: 'g2', cx: 0.08, cy: 0.72, r: 0.06, label_zh: '蜡烛火焰', label_en: 'Candle flame' },
      { id: 'g3', cx: 0.90, cy: 0.62, r: 0.06, label_zh: '右侧蜡烛', label_en: 'Right candle' },
      { id: 'g4', cx: 0.65, cy: 0.28, r: 0.07, label_zh: '幽灵颜色', label_en: 'Ghost color' },
      { id: 'g5', cx: 0.20, cy: 0.40, r: 0.07, label_zh: '镜子区域', label_en: 'Mirror area' },
    ],
  },
  {
    id: 'isaya',
    charId: 'isaya',
    charName: 'Isaya',
    baseImg: isayaBase,
    diffImg: isayaDiff,
    differences: [
      { id: 'i1', cx: 0.48, cy: 0.35, r: 0.07, label_zh: '猫咪颜色', label_en: 'Cat color' },
      { id: 'i2', cx: 0.15, cy: 0.45, r: 0.08, label_zh: '画板内容', label_en: 'Canvas painting' },
      { id: 'i3', cx: 0.55, cy: 0.12, r: 0.07, label_zh: '灯串颜色', label_en: 'Fairy lights' },
      { id: 'i4', cx: 0.20, cy: 0.88, r: 0.07, label_zh: '地面颜料', label_en: 'Floor paint' },
      { id: 'i5', cx: 0.82, cy: 0.60, r: 0.07, label_zh: '床上物品', label_en: 'Bed items' },
    ],
  },
  {
    id: 'isabel',
    charId: 'isabel',
    charName: 'Isabel',
    baseImg: isabelBase,
    diffImg: isabelDiff,
    differences: [
      { id: 'b1', cx: 0.48, cy: 0.25, r: 0.08, label_zh: '镜框颜色', label_en: 'Mirror frame' },
      { id: 'b2', cx: 0.72, cy: 0.42, r: 0.07, label_zh: '花瓶花朵', label_en: 'Flower vase' },
      { id: 'b3', cx: 0.20, cy: 0.15, r: 0.07, label_zh: '墙面颜色', label_en: 'Wall color' },
      { id: 'b4', cx: 0.68, cy: 0.68, r: 0.07, label_zh: '香水瓶', label_en: 'Perfume bottle' },
      { id: 'b5', cx: 0.88, cy: 0.35, r: 0.07, label_zh: '窗帘颜色', label_en: 'Curtain color' },
    ],
  },
];
