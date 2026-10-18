
import type { Job } from "../../types/job";
import Button from "../../components/ui/Button";
import JobResult from "./JobResult";
import {
  formatJobInput,
  formatJobTimestamp,
} from "./job-utils";

interface JobDetailsProps {
  job: Job;
  onClose: () => void;
}

export default function JobDetails({
  job,
  onClose,
}: JobDetailsProps) {
  return (
    <section className="job-details" aria-labelledby="job-details-title">
      <div className="job-details-heading">
        <div>
          <span className="job-form-eyebrow">JOB RECORD</span>
          <h2 id="job-details-title">{job.job_id}</h2>
        </div>

        <Button variant="text" onClick={onClose}>
          Close
        </Button>
      </div>

      <dl className="job-details-grid">
        <div>
          <dt>Status</dt>
          <dd>
            <span className={`job-status job-status--${job.status}`}>
              <span className="job-status-dot" />
              {job.status}
            </span>
          </dd>
        </div>

        <div>
          <dt>Worker ID</dt>
          <dd>{job.worker_id}</dd>
        </div>

        <div>
          <dt>Workload</dt>
          <dd>{job.workload_type}</dd>
        </div>

        <div>
          <dt>Input count</dt>
          <dd>{job.input_data.length}</dd>
        </div>

        <div>
          <dt>Created</dt>
          <dd>{formatJobTimestamp(job.created_at)}</dd>
        </div>

        <div>
          <dt>Last updated</dt>
          <dd>{formatJobTimestamp(job.updated_at)}</dd>
        </div>
      </dl>

      <div className="job-details-input">
        <h3>Input data</h3>
        <code>{formatJobInput(job.input_data)}</code>
      </div>

      <div className="job-details-result">
        <h3>Execution outcome</h3>
        <JobResult job={job} />
      </div>
    </section>
  );
}