
import type { Worker } from "../../types/worker";
import {
  formatBytes,
  getWorkerLabel,
  getWorkerOperatingSystem,
  getWorkerShortId,
} from "./worker-utils";

interface WorkerTableProps {
  workers: Worker[];
  onSelectWorker: (worker: Worker) => void;
}

export default function WorkerTable({
  workers,
  onSelectWorker,
}: WorkerTableProps) {
  return (
    <div className="worker-table-wrapper">
      <table className="worker-table">
        <thead>
          <tr>
            <th>WORKER</th>
            <th>PLATFORM</th>
            <th>OFFERED CPU</th>
            <th>OFFERED MEMORY</th>
            <th>STATUS</th>
          </tr>
        </thead>

        <tbody>
          {workers.map((worker) => {
            return (
              <tr
                key={worker.worker_id}
                className="worker-table-row"
                tabIndex={0}
                onClick={() => onSelectWorker(worker)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectWorker(worker);
                  }
                }}
                aria-label={`View details for ${getWorkerLabel(worker)}`}
              >
                <td>
                  <div className="worker-identity">
                    <span className="worker-machine-icon" aria-hidden="true">
                      ▦
                    </span>
                    <div>
                      <strong>{getWorkerLabel(worker)}</strong>
                      <span className="worker-id">
                        {getWorkerShortId(worker.worker_id)}
                      </span>
                    </div>
                  </div>
                </td>

                <td>{getWorkerOperatingSystem(worker)}</td>

                <td>
                  <strong>{worker.offered_cpu_cores}</strong>
                  <span className="worker-secondary">
                    {worker.offered_cpu_cores === 1 ? "core" : "cores"}
                  </span>
                </td>

                <td>
                  <div className="worker-memory">
                    <strong>{formatBytes(worker.offered_memory_bytes)}</strong>
                  </div>
                </td>

                <td>
                  <span
                    className={`worker-status worker-status--${worker.status}`}
                  >
                    <span className="worker-status-dot" />
                    {worker.status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}