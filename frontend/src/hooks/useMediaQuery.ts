import { useState, useEffect } from 'react';

export function useMediaQuery(query: string) {
  // Always start `false`, matching what the server renders (no `window`
  // there). Reading `window.matchMedia` synchronously in the initial state
  // meant the client's very first render (before hydration reconciles with
  // the server HTML) could already differ from the server — triggering a
  // React hydration mismatch/crash on any page using this hook (Footer runs
  // on every page).
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQueryList = window.matchMedia(query);
    setMatches(mediaQueryList.matches);

    const listener = (e: MediaQueryListEvent): void => setMatches(e.matches);
    mediaQueryList.addEventListener('change', listener);
    return () => mediaQueryList.removeEventListener('change', listener);
  }, [query]);

  return matches;
}
