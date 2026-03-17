import React, { useCallback } from 'react';
import type { BubbleMood } from '../hooks/useSpotDiffS2';
import { openProfile, isInAigram } from '../utils/aigram';

interface CharBubbleProps {
  charName: string;
  charImg: string;
  avatarUrl: string;
  telegramId: string;
  text: string | null;
  mood: BubbleMood;
  leaving?: boolean;
}

const CharBubble: React.FC<CharBubbleProps> = ({ charName, charImg, telegramId, text, mood, leaving }) => {
  if (!text) return null;

  const handlePortraitTap = useCallback(() => {
    if (telegramId && isInAigram()) {
      openProfile(telegramId);
    }
  }, [telegramId]);

  const tappable = !!telegramId && isInAigram();

  return (
    <div className={`sd__vn${leaving ? ' sd__vn--leaving' : ''}${mood === 'happy' ? ' sd__vn--happy' : ''}`}>
      <div
        className={`sd__vn-portrait${tappable ? ' sd__vn-portrait--tappable' : ''}`}
        onPointerDown={tappable ? handlePortraitTap : undefined}
      >
        <img src={charImg} alt={charName} draggable={false} />
      </div>
      <div className="sd__vn-box">
        <div className="sd__vn-name">{charName}</div>
        <div className="sd__vn-text">{text}</div>
      </div>
    </div>
  );
};

export default React.memo(CharBubble);
