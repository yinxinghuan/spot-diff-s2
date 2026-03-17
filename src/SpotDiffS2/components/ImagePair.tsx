import React, { useCallback, useRef } from 'react';
import type { LevelDef, DiffRegion } from '../types';
import DiffMarker from './DiffMarker';

interface ImagePairProps {
  level: LevelDef;
  foundIds: Set<string>;
  hintTarget: string | null;
  cooldown: boolean;
  onTap: (nx: number, ny: number) => void;
}

function SingleImage({
  src,
  alt,
  diffs,
  foundIds,
  hintTarget,
  cooldown,
  onTap,
}: {
  src: string;
  alt: string;
  diffs: DiffRegion[];
  foundIds: Set<string>;
  hintTarget: string | null;
  cooldown: boolean;
  onTap: (nx: number, ny: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (cooldown) return;
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width;
      const ny = (e.clientY - rect.top) / rect.height;
      onTap(nx, ny);
    },
    [onTap, cooldown]
  );

  return (
    <div
      className={`sd__image-wrap${cooldown ? ' sd__image-wrap--cooldown' : ''}`}
      ref={containerRef}
      onPointerDown={handlePointerDown}
    >
      <img
        className="sd__image"
        src={src}
        alt={alt}
        draggable={false}
      />
      {diffs.map((d) =>
        foundIds.has(d.id) ? (
          <DiffMarker key={d.id} cx={d.cx} cy={d.cy} r={d.r} type="found" />
        ) : hintTarget === d.id ? (
          <DiffMarker key={d.id} cx={d.cx} cy={d.cy} r={d.r} type="hint" />
        ) : null
      )}
    </div>
  );
}

const ImagePair: React.FC<ImagePairProps> = ({
  level,
  foundIds,
  hintTarget,
  cooldown,
  onTap,
}) => {
  return (
    <div className="sd__pair">
      <SingleImage
        src={level.baseImg}
        alt="Original"
        diffs={level.differences}
        foundIds={foundIds}
        hintTarget={hintTarget}
        cooldown={cooldown}
        onTap={onTap}
      />
      <div className="sd__divider">
        <span className="sd__divider-line" />
      </div>
      <SingleImage
        src={level.diffImg}
        alt="Modified"
        diffs={level.differences}
        foundIds={foundIds}
        hintTarget={hintTarget}
        cooldown={cooldown}
        onTap={onTap}
      />
    </div>
  );
};

export default React.memo(ImagePair);
