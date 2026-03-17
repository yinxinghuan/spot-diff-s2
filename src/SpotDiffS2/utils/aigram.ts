/**
 * Aigram system call utilities.
 * Requires running inside Aigram iframe with ?api_origin= in URL.
 */

function getApiOrigin(): string | null {
  return new URLSearchParams(window.location.search).get('api_origin');
}

function callSystem(fnName: string, params: Record<string, unknown> = {}) {
  const apiOrigin = getApiOrigin();
  if (!apiOrigin) return;
  // Use btoa as fallback — js-base64 not bundled here
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(params))));
  window.parent.postMessage(`${fnName}-${encoded}`, apiOrigin);
}

/** Open a user's Aigram profile page by their telegram_id */
export function openProfile(telegramId: string) {
  callSystem('AW.PROFILE.OPEN', { id: telegramId });
}

/** Whether the game is running inside Aigram iframe */
export function isInAigram(): boolean {
  return !!getApiOrigin();
}
