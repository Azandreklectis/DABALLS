import { Link } from "react-router-dom";
import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import ErrorMessage from "../../components/ui/ErrorMessage";
import LoadingState from "../../components/ui/LoadingState";
import PageHeader from "../../layout/PageHeader";
import { useJobs } from "../../hooks/useJobs";
import { useWorkers } from "../../hooks/useWorkers";
import { formatJobTimestamp } from "../jobs/job-utils";

export default function OverviewPage() {
  const jobsState = useJobs();
  const workersState = useWorkers();
  const jobs = jobsState.jobs;
  const workers = workersState.workers;
  const onlineWorkers = workers.filter((worker) => worker.status === "online");
  const queued = jobs.filter((job) => job.status === "queued").length;
  const running = jobs.filter((job) => job.status === "running").length;
  const completed = jobs.filter((job) => job.status === "completed").length;
  const failed = jobs.filter((job) => job.status === "failed").length;
  const cpuOffered = onlineWorkers.reduce(
    (sum, worker) => sum + worker.offered_cpu_cores, 0,
  );
  const memoryOffered = onlineWorkers.reduce(
    (sum, worker) => sum + worker.offered_memory_bytes, 0,
  );
  const recentJobs = [...jobs]
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at))
    .slice(0, 6);

  return (
    <section className="page-content">
      <PageHeader
        eyebrow="CLUSTER / OVERVIEW"
        title="Overview"
        description="Monitor your distributed compute network, advertised capacity, and workload progress."
        actions={
          <Button
            variant="secondary"
            onClick={() => {
              void jobsState.refresh();
              void workersState.refresh();
            }}
            loading={jobsState.refreshing || workersState.refreshing}
            disabled={jobsState.refreshing || workersState.refreshing}
          >
            Refresh
          </Button>
        }
      />

      {(jobsState.error || workersState.error) && (
        <ErrorMessage
          title="Some cluster data could not be refreshed"
          message={[workersState.error, jobsState.error].filter(Boolean).join(" ")}
        />
      )}

      <div className="worker-metrics">
        <article className="worker-metric">
          <span>ONLINE WORKERS</span>
          <strong>{workersState.loading ? "—" : onlineWorkers.length}</strong>
          <small>{workers.length} registered in total</small>
        </article>
        <article className="worker-metric">
          <span>OFFERED CPU CORES</span>
          <strong>{workersState.loading ? "—" : cpuOffered}</strong>
          <small>Online workers only</small>
        </article>
        <article className="worker-metric">
          <span>OFFERED MEMORY</span>
          <strong>
            {workersState.loading ? "—" : `${(memoryOffered / 1024 ** 3).toFixed(2)} GiB`}
          </strong>
          <small>Advertised capacity, not a reservation</small>
        </article>
        <article className="worker-metric">
          <span>TOTAL JOBS</span>
          <strong>{jobsState.loading ? "—" : jobs.length}</strong>
          <small>{queued} queued · {running} running</small>
        </article>
      </div>

      <div className="job-metrics">
        <article className="job-metric">
          <span>QUEUED</span>
          <strong>{jobsState.loading ? "—" : queued}</strong>
          <small>Waiting for execution</small>
        </article>
        <article className="job-metric">
          <span>RUNNING</span>
          <strong>{jobsState.loading ? "—" : running}</strong>
          <small>Currently executing</small>
        </article>
        <article className="job-metric">
          <span>COMPLETED</span>
          <strong>{jobsState.loading ? "—" : completed}</strong>
          <small>Finished successfully</small>
        </article>
        <article className="job-metric">
          <span>FAILED</span>
          <strong>{jobsState.loading ? "—" : failed}</strong>
          <small>Require investigation</small>
        </article>
      </div>

      <div className="overview-section-heading">
        <div>
          <h2>Recent jobs</h2>
          <p>Latest workloads recorded by the controller. Data refreshes automatically.</p>
        </div>
        <Link className="button button--secondary button--medium" to="/jobs">
          All jobs
        </Link>
      </div>

      {jobsState.loading ? (
        <LoadingState label="Loading recent jobs…" />
      ) : recentJobs.length === 0 ? (
        <EmptyState
          title="No workloads yet"
          description="Register an online worker, then submit a job to start using your compute network."
        />
      ) : (
        <div className="overview-recent-jobs">
          <div className="overview-job-row overview-job-row--header">
            <span>JOB</span>
            <span>WORKLOAD</span>
            <span>STATUS</span>
            <span>CREATED</span>
          </div>
          {recentJobs.map((job) => (
            <div className="overview-job-row" key={job.job_id}>
              <code title={job.job_id}>{job.job_id.slice(0, 12)}</code>
              <span>{job.workload_type}</span>
              <span className={`job-status job-status--${job.status}`}>
                <span className="job-status-dot" />
                {job.status}
              </span>
              <span>{formatJobTimestamp(job.created_at)}</span>
            </div>
          ))}
        </div>
      )}

      <div className="overview-quick-actions">
        <Link className="button button--primary button--medium" to="/jobs">
          Submit a workload
        </Link>
        <Link className="button button--secondary button--medium" to="/workers/register">
          Join a computer
        </Link>
        <Link className="button button--secondary button--medium" to="/workers">
          Manage workers
        </Link>
      </div>
    </section>
  );
}
