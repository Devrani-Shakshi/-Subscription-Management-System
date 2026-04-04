import { useState, useEffect, useCallback } from 'react';

interface BreakpointResult {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

const BREAKPOINTS = {
  mobile: '(max-width: 767px)',
  tablet: '(min-width: 768px) and (max-width: 1023px)',
  desktop: '(min-width: 1024px)',
} as const;

export function useBreakpoint(): BreakpointResult {
  const getMatches = useCallback((): BreakpointResult => {
    if (typeof window === 'undefined') {
      return { isMobile: false, isTablet: false, isDesktop: true };
    }

    return {
      isMobile: window.matchMedia(BREAKPOINTS.mobile).matches,
      isTablet: window.matchMedia(BREAKPOINTS.tablet).matches,
      isDesktop: window.matchMedia(BREAKPOINTS.desktop).matches,
    };
  }, []);

  const [breakpoint, setBreakpoint] = useState<BreakpointResult>(getMatches);

  useEffect(() => {
    const mobileQuery = window.matchMedia(BREAKPOINTS.mobile);
    const tabletQuery = window.matchMedia(BREAKPOINTS.tablet);
    const desktopQuery = window.matchMedia(BREAKPOINTS.desktop);

    const handler = () => setBreakpoint(getMatches());

    mobileQuery.addEventListener('change', handler);
    tabletQuery.addEventListener('change', handler);
    desktopQuery.addEventListener('change', handler);

    return () => {
      mobileQuery.removeEventListener('change', handler);
      tabletQuery.removeEventListener('change', handler);
      desktopQuery.removeEventListener('change', handler);
    };
  }, [getMatches]);

  return breakpoint;
}
