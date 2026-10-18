
import type { Worker } from "../../types/worker";
import {
  formatBytes,
  getWorkerLabel,
  getWorkerMemoryUsage,
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
            <th>CPU</th>
            <th>MEMORY</th>
            <th>OFFERED RESOURCES</th>
            <th>STATUS</th>
          </tr>
        </thead>

        <tbody>
          {workers.map((worker) => {
            const memoryUsage = getWorkerMemoryUsage(worker);

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
                  <strong>{worker.cpu_logical_cores}</strong>
                  <span className="worker-secondary">
                    {" "}logical cores
                  </span>
                </td>

                <td>
                  <div className="worker-memory">
                    <div className="worker-memory-label">
                      <strong>{formatBytes(worker.memory_available_bytes)}</strong>
                      <span>
                        / {formatBytes(worker.memory_total_bytes)}
                      </span>
                    </div>
                    <div
                      className="worker-memory-track"
                      role="progressbar"
                      aria-label={`${getWorkerLabel(worker)} memory used`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={Math.round(memoryUsage)}
                    >
                      <span style={{ width: `${memoryUsage}%` }} />
                    </div>
                    <span className="worker-secondary">
                      {Math.round(memoryUsage)}% used
                    </span>
                  </div>
                </td>

                <td>
                  <div className="worker-offers">
                    <span>{worker.offered_cpu_cores} CPU</span>
                    <span>
                      {formatBytes(worker.offered_memory_bytes)} RAM
                    </span>
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