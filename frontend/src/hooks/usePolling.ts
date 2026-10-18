
import { useEffect } from "react";

export function usePolling(
  callback: () => void,
  intervalMs: number,
  enabled = true,
): void {
  useEffect(() => {
    if (!enabled || intervalMs <= 0) {
      return;
    }

    const intervalId = window.setInterval(callback, intervalMs);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [callback, intervalMs, enabled]);
}