import { useEffect, useState } from 'react';

/**
 * Runs a client call and tracks its loading and error state.
 *
 * The callback is expected to come from `api/client`; this hook knows nothing
 * about where the data lives. Wrap `load` in `useCallback` — it is the only
 * dependency, so it decides when the call runs again.
 */
export function useAsync<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    load()
      .then((value) => {
        if (!cancelled) setData(value);
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : 'Something went wrong.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  return { data, error, loading, setData };
}
