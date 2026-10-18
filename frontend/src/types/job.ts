
export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed";

export type WorkloadType = "sum_integers";

export interface Job {
  job_id: string;
  worker_id: string;
  workload_type: WorkloadType;
  input_data: number[];
  status: JobStatus;
  result: number | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobSubmission {
  worker_id: string;
  workload_type: WorkloadType;
  input_data: number[];
}

export interface JobResultSubmission {
  worker_id: string;
  result?: number | null;
  error?: string | null;
}