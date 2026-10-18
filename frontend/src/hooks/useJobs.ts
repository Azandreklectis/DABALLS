
import { useCallback, useEffect, useState } from "react";
import { getJobs, submitJob } from "../api/jobs";
import type { Job, JobSubmission } from "../types/job";
import { usePolling } from "./usePolling";

const JOB_POLL_INTERVAL = 5000;

export function useJobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setRefreshing(true);

    try {
      const data = await getJobs();
      setJobs(data);
      setError(null);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load jobs.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const submit = useCallback(
    async (submission: JobSubmission): Promise<Job> => {
      setSubmitting(true);

      try {
        const createdJob = await submitJob(submission);
        setError(null);
        await refresh();
        return createdJob;
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to submit job.";
        setError(message);
        throw err;
      } finally {
        setSubmitting(false);
      }
    },
    [refresh],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  usePolling(() => {
    void refresh();
  }, JOB_POLL_INTERVAL);

  return {
    jobs,
    loading,
    refreshing,
    submitting,
    error,
    refresh,
    submit,
  };
}