import { useEffect, useState } from "react";

export default function usePersistedState<T>(key: string, initialValue: T) {
  const [state, setState] = useState<T>(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }

    try {
      const raw = window.localStorage.getItem(key);
      if (raw === null) {
        return initialValue;
      }
      
      // Try to parse the data
      const parsed = JSON.parse(raw);
      
      // Validate the parsed data against expected structure
      if (key.includes('benchmarkResult') && (!parsed || typeof parsed !== 'object' || !Array.isArray(parsed.variants))) {
        console.warn(`[DEBUG] Corrupted benchmarkResult data in localStorage, clearing it`);
        window.localStorage.removeItem(key);
        return initialValue;
      }
      
      if (key.includes('workflowCards') && (!Array.isArray(parsed))) {
        console.warn(`[DEBUG] Corrupted workflowCards data in localStorage, clearing it`);
        window.localStorage.removeItem(key);
        return initialValue;
      }
      
      return parsed as T;
    } catch (error) {
      console.warn(`[DEBUG] Error parsing localStorage key ${key}, clearing it:`, error);
      window.localStorage.removeItem(key);
      return initialValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(state));
    } catch {
      // Ignore storage quota/privacy mode errors.
    }
  }, [key, state]);

  return [state, setState] as const;
}
