import { useState } from "react";
import { useWorkers } from "../../hooks/useWorkers";
import type { Worker } from "../../types/worker";

import PageHeader from "../../layout/PageHeader";
import WorkerTable from "./WorkerTable";

import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import ErrorMessage from "../../components/ui/ErrorMessage";
import LoadingState from "../../components/ui/LoadingState";

import WorkerDetails from "./WorkerDetails";

export default function WorkersPage() {
  const {
    workers,
    loading,
    refreshing,
    error,
    refresh,
  } = useWorkers();

  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);

  const onlineCount = workers.filter(
    (worker) => worker.status === "online",
  ).length;

  const totalCpu = workers.reduce(
    (total, worker) => total + worker.cpu_logical_cores,
    0,
  );

  const totalMemory = workers.reduce(
    (total, worker) => total + worker.memory_total_bytes,
    0,
  );

  return (
    <section className="page-content">
      <PageHeader
        eyebrow="COMPUTE FLEET"
        title="Workers"
        description="Machines connected to your distributed compute environment."
        actions={
          <Button
            variant="secondary"
            onClick={() => void refresh()}
            loading={refreshing}
            disabled={refreshing}
          >
            Refresh
          </Button>
        }
      />

      <div className="worker-metrics">
        <article className="worker-metric">
          <span>REGISTERED WORKERS</span>
          <strong>{loading ? "—" : workers.length}</strong>
          <small>Known to the controller</small>
        </article>

        <article className="worker-metric">
          <span>ONLINE WORKERS</span>
          <strong>{loading ? "—" : onlineCount}</strong>
          <small>Currently marked online</small>
        </article>

        <article className="worker-metric">
          <span>LOGICAL CPU CORES</span>
          <strong>{loading ? "—" : totalCpu}</strong>
          <small>Across registered machines</small>
        </article>

        <article className="worker-metric">
          <span>TOTAL MEMORY</span>
          <strong>
            {loading
              ? "—"
              : `${(totalMemory / 1024 ** 3).toFixed(1)} GB`}
          </strong>
          <small>Reported physical memory</small>
        </article>
      </div>

      <div className="worker-section-heading">
        <div>
          <h2>Registered machines</h2>
          <p>Resource reports and connectivity status from the controller.</p>
        </div>
        <span className="worker-record-count">
          {loading ? "Loading…" : `${workers.length} records`}
        </span>
      </div>

      {error && (
        <ErrorMessage
          title="Unable to refresh workers"
          message={error}
          action={
            <Button variant="secondary" onClick={() => void refresh()}>
              Try again
            </Button>
          }
        />
      )}

      {loading ? (
        <LoadingState label="Loading worker records…" />
      ) : workers.length === 0 ? (
        <EmptyState
          title="No workers registered"
          description="When a worker connects and registers with the controller, its machine and resource information will appear here."
        />
      ) : (
        <WorkerTable
          workers={workers}
          onSelectWorker={setSelectedWorker}
        />
      )}
      {selectedWorker && (
          <WorkerDetails
              worker={selectedWorker}
              onClose={() => setSelectedWorker(null)}
          />
      )}
    </section>
  );
}