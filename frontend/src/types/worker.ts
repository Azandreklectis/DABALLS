
export type WorkerStatus = "online" | "offline";

export interface Worker {
  worker_id: string;
  display_name?: string | null;
  hostname: string;
  os_name: string;
  architecture: string;

  cpu_logical_cores: number;
  memory_total_bytes: number;
  memory_available_bytes: number;

  disk_total_bytes?: number | null;
  disk_free_bytes?: number | null;

  offered_cpu_cores: number;
  offered_memory_bytes: number;

  status: WorkerStatus;
  registered_at: string;
  last_seen_at: string;
}

export interface WorkerRegistration {
  worker_id: string;
  display_name?: string | null;
  hostname: string;
  os_name: string;
  architecture: string;

  cpu_logical_cores: number;
  memory_total_bytes: number;
  memory_available_bytes: number;

  disk_total_bytes?: number | null;
  disk_free_bytes?: number | null;

  offered_cpu_cores?: number;
  offered_memory_bytes?: number;
}