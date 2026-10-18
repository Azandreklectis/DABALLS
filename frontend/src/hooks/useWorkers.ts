
import { useCallback, useEffect, useState } from "react";
import { getWorkers } from "../api/workers";
import type { Worker } from "../types/worker";
import { usePolling } from "./usePolling";

const WORKER_POLL_INTERVAL = 5000;

export function useWorkers() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setRefreshing(true);

    try {
      const data = await getWorkers();
      setWorkers(data);
      setError(null);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load workers.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  usePolling(
    () => {
      void refresh();
    },
    WORKER_POLL_INTERVAL,
  );

  return {
    workers,
    loading,
    refreshing,
    error,
    refresh,
  };
}