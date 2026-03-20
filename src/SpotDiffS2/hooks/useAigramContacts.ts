import { useState, useEffect } from 'react';
import type { AigramContact } from '../types';

const MAX_CONTACTS = 6;

/** Demo contacts used when NOT running inside Aigram iframe */
const DEMO_CONTACTS: AigramContact[] = [
  { telegram_id: '1', name: 'Goat McFisty', head_url: '' },
  { telegram_id: '2', name: 'Capitan', head_url: '' },
  { telegram_id: '3', name: 'Chill guy', head_url: '' },
  { telegram_id: '4', name: 'Last Best', head_url: '' },
  { telegram_id: '5', name: 'KI_Bo', head_url: '' },
  { telegram_id: '6', name: 'Bonjour', head_url: '' },
];

function getUrlParams(): { apiOrigin: string | null; telegramId: string | null } {
  const params = new URLSearchParams(window.location.search);
  return {
    apiOrigin: params.get('api_origin'),
    telegramId: params.get('telegram_id'),
  };
}

function postMessageCall(
  apiOrigin: string,
  url: string,
  timeoutMs = 8000
): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const requestId = crypto.randomUUID();
    const payload = {
      url,
      method: 'GET',
      data: null,
      request_id: requestId,
      emitter: window.location.origin,
    };
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));

    const timer = setTimeout(() => {
      window.removeEventListener('message', handler);
      reject(new Error('API timeout'));
    }, timeoutMs);

    function handler(event: MessageEvent) {
      if (typeof event.data !== 'string') return;
      if (!event.data.startsWith('callAPIResult-')) return;
      try {
        const raw = event.data.slice('callAPIResult-'.length);
        const result = JSON.parse(decodeURIComponent(escape(atob(raw))));
        if (result.request_id !== requestId) return;
        clearTimeout(timer);
        window.removeEventListener('message', handler);
        if (!result.success) {
          reject(new Error(result.error || 'API error'));
          return;
        }
        resolve(result.data);
      } catch {
        // not our message
      }
    }

    window.addEventListener('message', handler);
    window.parent.postMessage(`callAPI-${encoded}`, apiOrigin);
  });
}

async function fetchUserName(apiOrigin: string, telegramId: string): Promise<string | null> {
  try {
    const data = await postMessageCall(
      apiOrigin,
      `/note/telegram/user/get/info/by/telegram_id?telegram_id=${telegramId}`,
      5000
    ) as { name?: string } | null;
    return data?.name || null;
  } catch {
    return null;
  }
}

async function fetchContactsViaPostMessage(
  apiOrigin: string,
  telegramId: string
): Promise<AigramContact[]> {
  const data = await postMessageCall(
    apiOrigin,
    `/note/telegram/user/contact/list?telegram_id=${telegramId}`,
    10000
  ) as Array<{ telegram_id: string; name?: string; head_url?: string }> | null;

  const raw: AigramContact[] = (Array.isArray(data) ? data : [])
    .slice(0, MAX_CONTACTS)
    .map((u) => ({
      telegram_id: String(u.telegram_id),
      name: u.name || '',
      head_url: u.head_url || '',
    }));

  if (raw.length === 0) return [];

  // Enrich contacts that have no name via individual user lookup
  const enriched = await Promise.all(
    raw.map(async (contact) => {
      if (contact.name) return contact;
      const name = await fetchUserName(apiOrigin, contact.telegram_id);
      return { ...contact, name: name || contact.telegram_id };
    })
  );

  return enriched;
}

export interface UseAigramContactsResult {
  contacts: AigramContact[];
  loading: boolean;
  error: string | null;
  isDemo: boolean;
}

export function useAigramContacts(): UseAigramContactsResult {
  const [contacts, setContacts] = useState<AigramContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    const { apiOrigin, telegramId } = getUrlParams();

    if (!apiOrigin || !telegramId) {
      // Not in Aigram iframe — use demo data
      setContacts(DEMO_CONTACTS);
      setIsDemo(true);
      setLoading(false);
      return;
    }

    fetchContactsViaPostMessage(apiOrigin, telegramId)
      .then((result) => {
        if (result.length === 0) {
          // Fallback to demo if user has no contacts
          setContacts(DEMO_CONTACTS);
          setIsDemo(true);
        } else {
          // Pad to 6 with demo contacts if fewer than 6 friends
          const padded = [...result];
          let demoIdx = 0;
          while (padded.length < MAX_CONTACTS && demoIdx < DEMO_CONTACTS.length) {
            if (!padded.find(c => c.name === DEMO_CONTACTS[demoIdx].name)) {
              padded.push(DEMO_CONTACTS[demoIdx]);
            }
            demoIdx++;
          }
          setContacts(padded.slice(0, MAX_CONTACTS));
          setIsDemo(false);
        }
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        setError(msg);
        setContacts(DEMO_CONTACTS);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, []);

  return { contacts, loading, error, isDemo };
}
