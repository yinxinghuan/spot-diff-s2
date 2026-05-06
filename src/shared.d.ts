declare module '@shared/leaderboard' {
  import type { FC } from 'react';
  export interface LeaderboardEntry { telegram_id: string; name: string; avatar_url: string; score: number; isMe?: boolean; }
  interface LeaderboardProps { gameName: string; isInAigram: boolean; onClose: () => void; fetchGlobal: () => Promise<LeaderboardEntry[]>; fetchFriends: () => Promise<LeaderboardEntry[]>; }
  export const Leaderboard: FC<LeaderboardProps>;
  interface GameScoreResult { isInAigram: boolean; telegramId: string | null; currentUser: { telegram_id: string; name: string; avatar_url: string } | null; submitScore: (score: number) => Promise<void>; fetchGlobalLeaderboard: () => Promise<LeaderboardEntry[]>; fetchFriendsLeaderboard: () => Promise<LeaderboardEntry[]>; }
  export function useGameScore(gameId: string): GameScoreResult;
}

declare module '@shared/save' {
  export interface UseGameSave<T> {
    savedData: T | null | undefined;
    loaded: boolean;
    hasSave: boolean;
    persist: (data: T) => void;
    clear: () => Promise<void>;
  }
  export function useGameSave<T>(gameId: string): UseGameSave<T>;
}
