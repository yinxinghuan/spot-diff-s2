import React from 'react';
import { t } from '../i18n';

interface HintButtonProps {
  hintsUsed: number;
  maxHints: number;
  onHint: () => void;
}

const HintButton: React.FC<HintButtonProps> = ({ hintsUsed, maxHints, onHint }) => {
  const remaining = maxHints - hintsUsed;
  const disabled = remaining <= 0;

  return (
    <button
      className={`sd__hint-btn${disabled ? ' sd__hint-btn--disabled' : ''}`}
      onPointerDown={disabled ? undefined : onHint}
      disabled={disabled}
    >
      {disabled ? t('noHints') : t('hintBtn', { n: remaining })}
    </button>
  );
};

export default React.memo(HintButton);
