import type { Worker } from "../../types/worker";
import Button from "../../components/ui/Button";
import Timestamp from "../../components/data-display/Timestamp";
import { formatBytes, getWorkerOperatingSystem } from "./worker-utils";

interface WorkerDetailsProps {
  worker: Worker;
  onClose: () => void;
}

export default function WorkerDetails({ worker, onClose }: WorkerDetailsProps) {
  const memoryUsed = Math.max(0, worker.memory_total_bytes - worker.memory_available_bytes);

  return (
    <aside className="worker-details" aria-labelledby="worker-details-title">
      <div className="worker-details-header">
        <div>
          <span className="worker-details-eyebrow">MACHINE RECORD</span>
          <h2 id="worker-details-title">{worker.display_name || worker.hostname}</h2>
          {worker.display_name && <p>{worker.hostname}</p>}
          <p>{worker.worker_id}</p>
        </div>
        <Button variant="text" onClick={onClose}>Close</Button>
      </div>

      <div className="worker-details-status">
        <span className={`worker-status worker-status--${worker.status}`}><span className="worker-status-dot" />{worker.status}</span>
        <span>{getWorkerOperatingSystem(worker)}</span>
      </div>

      <section className="worker-details-section">
        <h3>Hardware resources</h3>
        <dl className="worker-details-grid">
          <div><dt>Logical CPU cores</dt><dd>{worker.cpu_logical_cores}</dd></div>
          <div><dt>Available memory</dt><dd>{formatBytes(worker.memory_available_bytes)}</dd></div>
          <div><dt>Total memory</dt><dd>{formatBytes(worker.memory_total_bytes)}</dd></div>
          <div><dt>Estimated memory used</dt><dd>{formatBytes(memoryUsed)}</dd></div>
        </dl>
      </section>

      <section className="worker-details-section">
        <h3>Resource contribution</h3>
        <dl className="worker-details-grid">
          <div><dt>Offered CPU cores</dt><dd>{worker.offered_cpu_cores}</dd></div>
          <div><dt>Offered memory</dt><dd>{formatBytes(worker.offered_memory_bytes)}</dd></div>
        </dl>
      </section>

      <section className="worker-details-section">
        <h3>Connection history</h3>
        <dl className="worker-details-grid">
          <div><dt>Registered</dt><dd><Timestamp value={worker.registered_at} format="absolute" /></dd></div>
          <div><dt>Last seen</dt><dd><Timestamp value={worker.last_seen_at} format="absolute" /></dd></div>
        </dl>
      </section>
    </aside>
  );
}
