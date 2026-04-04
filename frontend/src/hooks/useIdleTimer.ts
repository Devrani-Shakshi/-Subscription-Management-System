import { useEffect, useRef, useCallback, useState } from 'react';
import type { Role } from '@/types';

const IDLE_TIMEOUTS: Record<Role, number> = {
  super_admin: 30 * 60 * 1000, // 30 min
  company: 30 * 60 * 1000,     // 30 min
  portal_user: 60 * 60 * 1000, // 60 min
};

const WARNING_BEFORE = 60 * 1000; // 60 seconds before timeout

interface IdleTimerResult {
  isWarning: boolean;
  remainingSeconds: number;
  resetTimer: () => void;
}

export function useIdleTimer(role: Role): IdleTimerResult {
  const [isWarning, setIsWarning] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const warningRef = useRef<ReturnType<typeof setTimeout>>();
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const timeout = IDLE_TIMEOUTS[role];

  const resetTimer = useCallback(() => {
    setIsWarning(false);
    setRemainingSeconds(0);

    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningRef.current) clearTimeout(warningRef.current);
    if (intervalRef.current) clearInterval(intervalRef.current);

    // Start warning countdown 60s before timeout
    warningRef.current = setTimeout(() => {
      setIsWarning(true);
      setRemainingSeconds(WARNING_BEFORE / 1000);

      intervalRef.current = setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }, timeout - WARNING_BEFORE);

    // Fire timeout event
    timeoutRef.current = setTimeout(() => {
      window.dispatchEvent(new CustomEvent('idle-timeout'));
    }, timeout);
  }, [timeout]);

  useEffect(() => {
    const events = ['mousemove', 'keydown', 'touchstart', 'mousedown', 'scroll'] as const;
    const handler = () => resetTimer();

    events.forEach((event) => window.addEventListener(event, handler));
    resetTimer();

    return () => {
      events.forEach((event) => window.removeEventListener(event, handler));
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningRef.current) clearTimeout(warningRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [resetTimer]);

  return { isWarning, remainingSeconds, resetTimer };
}
