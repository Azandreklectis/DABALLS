
import { apiRequest } from "./client";
import type { Worker, WorkerRegistration } from "../types/worker";

export function getWorkers(): Promise<Worker[]> {
  return apiRequest<Worker[]>("/v1/workers");
}

export function registerWorker(
  worker: WorkerRegistration,
): Promise<Worker> {
  return apiRequest<Worker>("/v1/workers/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(worker),
  });
}

export function sendWorkerHeartbeat(
  workerId: string,
): Promise<Worker> {
  return apiRequest<Worker>(
    `/v1/workers/${encodeURIComponent(workerId)}/heartbeat`,
    {
      method: "POST",
    },
  );
}