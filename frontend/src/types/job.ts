export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed";

export type WorkloadType = "sum_integers" | "python_package";

export interface Job {
  job_id: string;
  worker_id: string;
  workload_type: WorkloadType;
  input_data: number[] | null;
  artifact_id?: string | null;
  required_cpu_cores: number;
  required_memory_bytes: number;
  status: JobStatus;
  result: number | null;
  result_data?: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobSubmission {
  worker_id?: string;
  workload_type: WorkloadType;
  input_data?: number[];
  artifact_id?: string;
  required_cpu_cores: number;
  required_memory_bytes: number;
}

export interface JobResultSubmission {
  worker_id: string;
  result?: number | null;
  result_data?: Record<string, unknown> | null;
  error?: string | null;
}
