import React from 'react';
import type { LevelDef, SaveData } from '../types';
import { t } from '../i18n';
import { openProfile, isInAigram } from '../utils/aigram';

const SCENE_LABELS: Record<string, { zh: string; en: string }> = {
  occult:  { zh: '占卜室', en: 'Occult Den' },
  command: { zh: '指挥室', en: 'Command Room' },
  lounge:  { zh: '休闲厅', en: 'Lounge' },
  manor:   { zh: '庄园厅', en: 'Manor Hall' },
  temple:  { zh: '圣堂', en: 'Temple' },
  gym:     { zh: '拳馆', en: 'Boxing Gym' },
};

interface LevelSelectProps {
  levels: LevelDef[];
  save: SaveData;
  onSelect: (levelId: string) => void;
  onBack: () => void;
}

const LevelSelect: React.FC<LevelSelectProps> = ({ levels, save, onSelect, onBack }) => {
  const locale = navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
  const inAigram = isInAigram();

  return (
    <div className="sd__select">
      <h2 className="sd__select-title">{t('selectLevel')}</h2>
      <div className="sd__select-grid">
        {levels.map((level, idx) => {
          const unlocked = idx < save.unlocked;
          const result = save.results[level.id];
          const sceneLabel = SCENE_LABELS[level.id]?.[locale] ?? level.id;
          return (
            <div
              key={level.id}
              className={`sd__select-card${unlocked ? '' : ' sd__select-card--locked'}`}
              onPointerDown={unlocked ? () => onSelect(level.id) : undefined}
            >
              {/* Avatar — tappable to open profile in Aigram */}
              <div
                className={`sd__select-card-bg${inAigram && level.telegramId ? ' sd__select-card-bg--tappable' : ''}`}
                onPointerDown={inAigram && level.telegramId ? (e) => {
                  e.stopPropagation();
                  openProfile(level.telegramId);
                } : undefined}
              >
                <img src={level.cardImg} alt="" draggable={false} />
              </div>
              <div className="sd__select-card-info">
                <div className="sd__select-card-num">{idx + 1}</div>
                <div className="sd__select-card-name">{level.charName}</div>
                <div className="sd__select-card-scene">{sceneLabel}</div>
                {result ? (
                  <div className="sd__select-card-stars">
                    {'★'.repeat(result.stars)}{'☆'.repeat(3 - result.stars)}
                  </div>
                ) : unlocked ? (
                  <div className="sd__select-card-stars sd__select-card-stars--empty">☆☆☆</div>
                ) : (
                  <div className="sd__select-card-lock">🔒</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <button className="sd__btn sd__btn--back" onPointerDown={onBack}>
        {t('homeBtn')}
      </button>
    </div>
  );
};

export default React.memo(LevelSelect);
