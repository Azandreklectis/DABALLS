import { useState } from "react";
import { useJobs } from "../../hooks/useJobs";
import { useWorkers } from "../../hooks/useWorkers";
import PageHeader from "../../layout/PageHeader";
import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import ErrorMessage from "../../components/ui/ErrorMessage";
import LoadingState from "../../components/ui/LoadingState";
import JobTable from "./JobTable";
import SubmitJobForm from "./SubmitJobForm";
import JobDetails from "./JobDetails";

export default function JobsPage() {
  const { jobs, loading, refreshing, submitting, error, refresh, submit } = useJobs();
  const { workers, loading: workersLoading } = useWorkers();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const selectedJob = jobs.find((job) => job.job_id === selectedJobId) ?? null;

  const countByStatus = {
    queued: jobs.filter((job) => job.status === "queued").length,
    running: jobs.filter((job) => job.status === "running").length,
    completed: jobs.filter((job) => job.status === "completed").length,
    failed: jobs.filter((job) => job.status === "failed").length,
  };

  return (
    <section className="page-content">
      <PageHeader
        eyebrow="WORKLOAD CONTROL"
        title="Jobs"
        description="Submit work to registered machines and inspect execution results."
        actions={<Button variant="secondary" onClick={() => void refresh()} loading={refreshing} disabled={refreshing}>Refresh</Button>}
      />

      <div className="job-metrics">
        <article className="job-metric"><span>TOTAL JOBS</span><strong>{loading ? "—" : jobs.length}</strong><small>Recorded by the controller</small></article>
        <article className="job-metric"><span>QUEUED</span><strong>{loading ? "—" : countByStatus.queued}</strong><small>Awaiting execution</small></article>
        <article className="job-metric"><span>RUNNING</span><strong>{loading ? "—" : countByStatus.running}</strong><small>Currently executing</small></article>
        <article className="job-metric"><span>COMPLETED</span><strong>{loading ? "—" : countByStatus.completed}</strong><small>Finished successfully</small></article>
      </div>

      <div className="jobs-workspace">
        <div className="jobs-list-section">
          <div className="job-section-heading">
            <div><h2>Job records</h2><p>Live job state from the controller.</p></div>
            <span>{loading ? "Loading…" : `${jobs.length} records`}</span>
          </div>

          {error && <ErrorMessage title="Unable to load jobs" message={error} action={<Button variant="secondary" onClick={() => void refresh()}>Try again</Button>} />}

          {loading ? <LoadingState label="Loading jobs…" /> : jobs.length === 0 ? (
            <EmptyState title="No jobs recorded" description="Submit a workload to a registered worker to create your first job." />
          ) : (
            <JobTable jobs={jobs} onSelectJob={(job) => setSelectedJobId(job.job_id)} />
          )}

          {selectedJob && <JobDetails job={selectedJob} onClose={() => setSelectedJobId(null)} />}
        </div>

        <aside className="jobs-submit-section">
          {workersLoading ? <LoadingState label="Loading available workers…" /> : (
            <SubmitJobForm workers={workers} submitting={submitting} onSubmit={submit} />
          )}
        </aside>
      </div>
    </section>
  );
}
