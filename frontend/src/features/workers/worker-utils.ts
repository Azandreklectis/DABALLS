
import type { Worker } from "../../types/worker";

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    return "—";
  }

  if (bytes === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  const unitIndex = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  const value = bytes / 1024 ** unitIndex;
  const digits = value >= 100 ? 0 : value >= 10 ? 1 : 2;

  return `${value.toFixed(digits)} ${units[unitIndex]}`;
}

export function getWorkerLabel(worker: Worker): string {
  return worker.hostname || worker.worker_id;
}

export function getWorkerShortId(workerId: string): string {
  return workerId.length > 16
    ? `${workerId.slice(0, 8)}…${workerId.slice(-5)}`
    : workerId;
}

export function getWorkerOperatingSystem(worker: Worker): string {
  return `${worker.os_name} · ${worker.architecture}`;
}

export function getWorkerMemoryUsage(worker: Worker): number {
  if (worker.memory_total_bytes <= 0) {
    return 0;
  }

  const used =
    worker.memory_total_bytes - worker.memory_available_bytes;

  return Math.min(
    100,
    Math.max(0, (used / worker.memory_total_bytes) * 100),
  );
}