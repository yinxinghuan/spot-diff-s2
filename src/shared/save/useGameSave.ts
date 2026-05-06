import { useCallback, useEffect, useRef, useState } from 'react';

const GAMES_API = 'https://games-api.xinghuan-yin.workers.dev';

function getTelegramId(): string | null {
  return new URLSearchParams(window.location.search).get('telegram_id');
}

export interface UseGameSave<T> {
  /** Initial save loaded from cloud / localStorage. `undefined` while loading, `null` if no save exists. */
  savedData: T | null | undefined;
  /** True once the initial probe completed (regardless of whether a save was found). */
  loaded: boolean;
  /** Convenience: true when a save exists. */
  hasSave: boolean;
  /** Persist save data. Synchronously to localStorage; cloud write debounced (1s) and fire-and-forget. */
  persist: (data: T) => void;
  /** Erase save from cloud + localStorage. */
  clear: () => Promise<void>;
}

/**
 * Per-user save sync. Mirrors the {@link useGameScore} pattern:
 * cloud writes are namespaced by `telegram_id` from URL params (Aigram miniapp);
 * localStorage is the offline fallback and source of truth between writes.
 */
export function useGameSave<T>(gameId: string): UseGameSave<T> {
  const [savedData, setSavedData] = useState<T | null | undefined>(undefined);
  const lsKey = `${gameId}-save`;
  const telegramId = getTelegramId();
  const cloudTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingCloudRef = useRef<string | null>(null);

  // Initial load: cloud → localStorage → null
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (telegramId) {
        try {
          const res = await fetch(`${GAMES_API}/save?game_id=${gameId}&telegram_id=${telegramId}`);
          if (res.ok) {
            const json = await res.json();
            if (json && typeof json.data === 'string') {
              try {
                const save = JSON.parse(json.data) as T;
                if (!cancelled) setSavedData(save);
                return;
              } catch { /* corrupt cloud save — fall through to local */ }
            }
          }
        } catch { /* network — fall through */ }
      }
      try {
        const raw = localStorage.getItem(lsKey);
        if (raw) {
          const save = JSON.parse(raw) as T;
          if (!cancelled) setSavedData(save);
          return;
        }
      } catch { /* corrupt local — fall through */ }
      if (!cancelled) setSavedData(null);
    })();
    return () => { cancelled = true; };
  }, [gameId, telegramId, lsKey]);

  const flushCloud = useCallback(() => {
    const body = pendingCloudRef.current;
    pendingCloudRef.current = null;
    cloudTimerRef.current = null;
    if (!body || !telegramId) return;
    fetch(`${GAMES_API}/save`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body,
    }).catch(() => { /* ignore */ });
  }, [telegramId]);

  const persist = useCallback((data: T) => {
    const withTs = { ...(data as object), _lastActive: Date.now() };
    const json = JSON.stringify(withTs);
    try {
      localStorage.setItem(lsKey, json);
    } catch { /* quota / private mode */ }
    if (telegramId) {
      pendingCloudRef.current = JSON.stringify({ game_id: gameId, telegram_id: telegramId, data: json });
      if (cloudTimerRef.current) clearTimeout(cloudTimerRef.current);
      cloudTimerRef.current = setTimeout(flushCloud, 1000);
    }
  }, [gameId, telegramId, lsKey, flushCloud]);

  // Flush any pending write on unmount so we don't lose the latest save.
  useEffect(() => {
    return () => {
      if (cloudTimerRef.current) {
        clearTimeout(cloudTimerRef.current);
        flushCloud();
      }
    };
  }, [flushCloud]);

  const clear = useCallback(async () => {
    if (cloudTimerRef.current) { clearTimeout(cloudTimerRef.current); cloudTimerRef.current = null; }
    pendingCloudRef.current = null;
    try {
      localStorage.removeItem(lsKey);
    } catch { /* ignore */ }
    if (telegramId) {
      // Use the same PUT endpoint as persist (write empty payload) so we don't
      // depend on the worker implementing DELETE.
      try {
        await fetch(`${GAMES_API}/save`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: gameId, telegram_id: telegramId, data: '' }),
        });
      } catch { /* ignore */ }
    }
    setSavedData(null);
  }, [gameId, telegramId, lsKey]);

  return {
    savedData,
    loaded: savedData !== undefined,
    hasSave: savedData != null,
    persist,
    clear,
  };
}
