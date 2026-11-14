import { useCallback, useEffect, useState } from "react";

// Loads data with `fn`, optionally re-polling every `intervalMs`. Returns {data, error, loading, reload}.
export function useFetch(fn, intervalMs = 0, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setData(await fn());
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
    if (!intervalMs) return undefined;
    const t = setInterval(load, intervalMs);
    return () => clearInterval(t);
  }, [load, intervalMs]);

  return { data, error, loading, reload: load };
}
