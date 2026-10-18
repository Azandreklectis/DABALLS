
import { apiRequest } from "./client";
import type {
  Job,
  JobSubmission,
  JobResultSubmission,
} from "../types/job";

/**
 * Fetch all jobs recorded by the controller.
 */
export function getJobs(): Promise<Job[]> {
  return apiRequest<Job[]>("/v1/jobs");
}

/**
 * Fetch a single job by its ID.
 */
export function getJob(jobId: string): Promise<Job> {
  return apiRequest<Job>(
    `/v1/jobs/${encodeURIComponent(jobId)}`,
  );
}

/**
 * Submit a job to a specific worker.
 */
export function submitJob(
  submission: JobSubmission,
): Promise<Job> {
  return apiRequest<Job>("/v1/jobs", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(submission),
  });
}

/**
 * Report a job result from a worker.
 */
export function reportJobResult(
  jobId: string,
  submission: JobResultSubmission,
): Promise<Job> {
  return apiRequest<Job>(
    `/v1/jobs/${encodeURIComponent(jobId)}/result`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(submission),
    },
  );
}