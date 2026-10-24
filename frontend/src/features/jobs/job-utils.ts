
import type { Job, JobStatus } from "../../types/job";

export function getJobShortId(jobId: string): string {
  return jobId.length > 18
    ? `${jobId.slice(0, 10)}…${jobId.slice(-5)}`
    : jobId;
}

export function getJobStatusLabel(status: JobStatus): string {
  const labels: Record<JobStatus, string> = {
    queued: "Queued",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
  };

  return labels[status];
}

export function formatJobInput(input: number[] | null): string {
  if (input === null) {
    return "Input bundled in workload package";
  }

  if (input.length <= 4) {
    return input.join(", ");
  }

  return `${input.slice(0, 4).join(", ")}, … (${input.length} values)`;
}

export function formatJobTimestamp(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function getJobSummary(job: Job): string {
  if (job.status === "failed") {
    return job.error || "Job failed";
  }

  if (job.status === "completed") {
    return job.result === null ? "Completed" : `Result: ${job.result}`;
  }

  return job.status === "running" ? "Execution in progress" : "Awaiting execution";
}