import React, { useState } from 'react';
import { useSpotDiffS2 } from './hooks/useSpotDiffS2';
import { t, getLocale } from './i18n';
import SplashScreen from './components/SplashScreen';
import LevelSelect from './components/LevelSelect';
import ImagePair from './components/ImagePair';
import CharBubble from './components/CharBubble';
import HintButton from './components/HintButton';
import aigramLogo from './img/aigram.svg';
import { playClick, resumeAudio } from './utils/sounds';
import './SpotDiff.less';

const POINTS_PER_FIND = 100;

const SpotDiffS2: React.FC = () => {
  const [showSplash, setShowSplash] = useState(true);
  const {
    phase,
    save,
    currentLevel,
    foundIds,
    time,
    errors,
    hintsUsed,
    maxHints,
    lastResult,
    isNewRecord,
    bubbleText,
    bubbleMood,
    bubbleLeaving,
    cooldown,
    hintTarget,
    levels,
    goHome,
    goToSelect,
    startLevel,
    handleTap,
    useHint,
    nextLevel,
  } = useSpotDiffS2();

  // Show splash screen until contacts & assets are loaded
  if (showSplash || phase === 'loading') {
    return (
      <SplashScreen
        levels={levels}
        onDone={() => setShowSplash(false)}
      />
    );
  }

  return (
    <div className="sd">
      {/* Watermark */}
      <img className="sd__watermark" src={aigramLogo} alt="" draggable={false} />

      {/* === IDLE / Title Screen === */}
      {phase === 'idle' && (
        <div className="sd__title">
          <div className="sd__title-top">
            <div className="sd__title-magnifier">🔍</div>
            <div className="sd__title-badge">SEASON II</div>
          </div>
          <div className="sd__title-center">
            <div className="sd__title-line" />
            <h1 className="sd__title-name">{t('title')}</h1>
            <div className="sd__title-line" />
            <p className="sd__title-sub">{t('subtitle')}</p>
          </div>
          <div className="sd__title-deco">
            <span>6 CASES</span>
            <span>·</span>
            <span>🔎 🕵️ 📋</span>
          </div>
          <div className="sd__title-bottom">
            <button
              className="sd__btn sd__btn--start"
              onPointerDown={() => { resumeAudio(); playClick(); goToSelect(); }}
            >
              {t('startBtn')}
            </button>
          </div>
          <img className="sd__title-watermark" src={aigramLogo} alt="" draggable={false} />
        </div>
      )}

      {/* === Level Select === */}
      {phase === 'select' && (
        <LevelSelect
          levels={levels}
          save={save}
          onSelect={startLevel}
          onBack={goHome}
        />
      )}

      {/* === Playing === */}
      {phase === 'playing' && currentLevel && (
        <>
          {/* Header */}
          <div className="sd__header">
            <div className="sd__stat">
              <span className="sd__stat-label">{t('found')}</span>
              <span className="sd__stat-value">{foundIds.size}/{currentLevel.differences.length}</span>
            </div>
            <div className="sd__stat">
              <span className="sd__stat-label">{t('time')}</span>
              <span className="sd__stat-value">{time}s</span>
            </div>
            <div className="sd__stat">
              <span className="sd__stat-label">{t('errors')}</span>
              <span className="sd__stat-value">{errors}</span>
            </div>
          </div>

          {/* Image pair */}
          <ImagePair
            level={currentLevel}
            foundIds={foundIds}
            hintTarget={hintTarget}
            cooldown={cooldown}
            onTap={handleTap}
          />

          {/* Bottom bar */}
          <div className="sd__bottom">
            <div className="sd__bottom-actions">
              <HintButton hintsUsed={hintsUsed} maxHints={maxHints} onHint={useHint} />
              <button className="sd__btn sd__btn--quit" onPointerDown={goToSelect}>
                {t('homeBtn')}
              </button>
            </div>
          </div>

          {/* VN-style character dialogue overlay */}
          <CharBubble
            charName={currentLevel.charName}
            charImg={currentLevel.charImg}
            avatarUrl={currentLevel.avatarUrl}
            telegramId={currentLevel.telegramId}
            text={bubbleText}
            mood={bubbleMood}
            leaving={bubbleLeaving}
          />
        </>
      )}

      {/* === Level Complete === */}
      {phase === 'complete' && lastResult && currentLevel && (
        <div className="sd__overlay">
          <div className="sd__modal sd__modal--complete">
            <div className="sd__modal-icon">
              {'★'.repeat(lastResult.stars)}{'☆'.repeat(3 - lastResult.stars)}
            </div>
            <h2 className="sd__modal-title sd__modal-title--complete">{t('complete')}</h2>
            <div className="sd__clues">
              {currentLevel.differences.map(d => (
                <div key={d.id} className="sd__clue">
                  <span className="sd__clue-emoji">{d.emoji}</span>
                  <span className="sd__clue-label">{getLocale() === 'zh' ? d.label_zh : d.label_en}</span>
                </div>
              ))}
            </div>
            {isNewRecord && <div className="sd__new-record">{t('newRecord')}</div>}
            <div className="sd__result">
              <div className="sd__result-row">
                <span>{t('found')}</span>
                <strong>{currentLevel.differences.length} × {POINTS_PER_FIND}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('timeBonus')}</span>
                <strong>+{Math.max(0, 300 - lastResult.time * 2)}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('errorPenalty')}</span>
                <strong>-{lastResult.errors * 15}</strong>
              </div>
              <div className="sd__result-row">
                <span>{t('hintPenalty')}</span>
                <strong>-{lastResult.hints * 30}</strong>
              </div>
              <div className="sd__result-row sd__result-row--total">
                <span>{t('totalScore')}</span>
                <strong>{lastResult.score}</strong>
              </div>
            </div>
            <div className="sd__modal-actions">
              <button className="sd__btn sd__btn--start" onPointerDown={nextLevel}>
                {t('nextLevel')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={() => startLevel(currentLevel.id)}>
                {t('replayBtn')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={goToSelect}>
                {t('homeBtn')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* === All Clear === */}
      {phase === 'allClear' && (
        <div className="sd__overlay">
          <div className="sd__modal sd__modal--complete">
            <div className="sd__modal-icon">🏆</div>
            <h2 className="sd__modal-title">{t('allClear')}</h2>
            <p className="sd__modal-sub">{t('allClearSub')}</p>
            <div className="sd__modal-actions">
              <button className="sd__btn sd__btn--start" onPointerDown={goToSelect}>
                {t('selectLevel')}
              </button>
              <button className="sd__btn sd__btn--back" onPointerDown={goHome}>
                {t('homeBtn')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpotDiffS2;
