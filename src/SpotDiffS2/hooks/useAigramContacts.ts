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

async function fetchContactsViaPostMessage(
  apiOrigin: string,
  telegramId: string
): Promise<AigramContact[]> {
  return new Promise((resolve, reject) => {
    const requestId = crypto.randomUUID();

    const payload = {
      url: `/note/telegram/user/contact/list?telegram_id=${telegramId}`,
      method: 'GET',
      data: null,
      request_id: requestId,
      emitter: window.location.origin,
    };

    // Use js-base64 loaded via CDN on the page, or inline btoa
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(payload))));

    const timeout = setTimeout(() => {
      window.removeEventListener('message', handler);
      reject(new Error('API timeout'));
    }, 10000);

    function handler(event: MessageEvent) {
      if (typeof event.data !== 'string') return;
      if (!event.data.startsWith('callAPIResult-')) return;

      try {
        const raw = event.data.slice('callAPIResult-'.length);
        const result = JSON.parse(decodeURIComponent(escape(atob(raw))));
        if (result.request_id !== requestId) return;

        clearTimeout(timeout);
        window.removeEventListener('message', handler);

        if (!result.success) {
          reject(new Error(result.error || 'API error'));
          return;
        }

        const contacts: AigramContact[] = (result.data || [])
          .slice(0, MAX_CONTACTS)
          .map((u: { telegram_id: string; name: string; domain_sub_name?: string; head_url: string }) => ({
            telegram_id: String(u.telegram_id),
            name: u.domain_sub_name || u.name,
            head_url: u.head_url || '',
          }));

        resolve(contacts);
      } catch {
        // not our message, ignore
      }
    }

    window.addEventListener('message', handler);
    window.parent.postMessage(`callAPI-${encoded}`, apiOrigin);
  });
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
