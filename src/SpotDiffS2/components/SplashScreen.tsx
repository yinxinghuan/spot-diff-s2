import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { LevelDef } from '../types';
import posterImg from '../img/poster.png';

const MIN_MS = 2200;
const MAX_ASSET_MS = 10000;

interface SplashScreenProps {
  levels: LevelDef[];
  onDone: () => void;
  waitFor?: boolean;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ levels, onDone, waitFor }) => {
  const [posterReady, setPosterReady] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fading, setFading] = useState(false);
  const [minDone, setMinDone] = useState(false);
  const [assetsDone, setAssetsDone] = useState(false);
  const doneCalledRef = useRef(false);

  useEffect(() => {
    const timer = setTimeout(() => setMinDone(true), MIN_MS);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const images = levels.flatMap(l => [l.baseImg, l.diffImg]);
    const total = images.length;
    if (total === 0) {
      setAssetsDone(true);
      return;
    }
    let loaded = 0;
    const timeout = setTimeout(() => setAssetsDone(true), MAX_ASSET_MS);

    images.forEach((src) => {
      const img = new Image();
      img.onload = img.onerror = () => {
        loaded += 1;
        setProgress(Math.round((loaded / total) * 100));
        if (loaded === total) {
          clearTimeout(timeout);
          setAssetsDone(true);
        }
      };
      img.src = src;
    });

    return () => clearTimeout(timeout);
  }, [levels]);

  const triggerFade = useCallback(() => {
    if (doneCalledRef.current) return;
    doneCalledRef.current = true;
    setFading(true);
    setTimeout(onDone, 500);
  }, [onDone]);

  useEffect(() => {
    if (minDone && assetsDone && !waitFor) triggerFade();
  }, [minDone, assetsDone, waitFor, triggerFade]);

  return (
    <div className={`sd-splash${fading ? ' sd-splash--fading' : ''}`}>
      <img
        className={`sd-splash__img${posterReady ? ' sd-splash__img--visible' : ''}`}
        src={posterImg}
        alt="Spot the Difference II"
        draggable={false}
        onLoad={() => setPosterReady(true)}
      />
      <div className="sd-splash__bar-track">
        <div
          className="sd-splash__bar-fill"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

export default React.memo(SplashScreen);
