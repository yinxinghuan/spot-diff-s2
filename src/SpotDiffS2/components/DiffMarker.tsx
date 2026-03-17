import React from 'react';

interface DiffMarkerProps {
  cx: number;
  cy: number;
  r: number;
  type: 'found' | 'hint';
}

const DiffMarker: React.FC<DiffMarkerProps> = ({ cx, cy, r, type }) => {
  // Use width only + aspect-ratio:1 in CSS for perfect circle
  const size = `${r * 200}%`;
  const style: React.CSSProperties = {
    left: `${cx * 100}%`,
    top: `${cy * 100}%`,
    width: size,
  };

  return (
    <div
      className={`sd__marker sd__marker--${type}`}
      style={style}
    />
  );
};

export default React.memo(DiffMarker);
