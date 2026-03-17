import React from 'react';
import type { LevelDef, SaveData } from '../types';
import { t } from '../i18n';

// Scene theme labels shown on cards
const SCENE_LABELS: Record<string, { zh: string; en: string }> = {
  cafe:    { zh: '咖啡馆', en: 'Café' },
  vinyl:   { zh: '唱片店', en: 'Record Store' },
  bar:     { zh: '酒吧', en: 'Bar' },
  library: { zh: '图书馆', en: 'Library' },
  kitchen: { zh: '厨房', en: 'Kitchen' },
  rooftop: { zh: '屋顶', en: 'Rooftop' },
};

interface LevelSelectProps {
  levels: LevelDef[];
  save: SaveData;
  onSelect: (levelId: string) => void;
  onBack: () => void;
}

const LevelSelect: React.FC<LevelSelectProps> = ({ levels, save, onSelect, onBack }) => {
  const locale = navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';

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
              {/* Avatar as card background */}
              <div className="sd__select-card-bg">
                {level.avatarUrl ? (
                  <img src={level.avatarUrl} alt="" draggable={false} />
                ) : (
                  <div className="sd__select-card-avatar-fallback">
                    {level.charName.charAt(0).toUpperCase()}
                  </div>
                )}
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
