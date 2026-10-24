
import type { Job } from "../../types/job";
import {
  formatJobInput,
  formatJobTimestamp,
  getJobShortId,
  getJobStatusLabel,
} from "./job-utils";

interface JobTableProps {
  jobs: Job[];
  onSelectJob: (job: Job) => void;
}

export default function JobTable({
  jobs,
  onSelectJob,
}: JobTableProps) {
  return (
    <div className="job-table-wrapper">
      <table className="job-table">
        <thead>
          <tr>
            <th>JOB</th>
            <th>WORKLOAD</th>
            <th>INPUT / PACKAGE</th>
            <th>WORKER</th>
            <th>SUBMITTED</th>
            <th>STATUS</th>
          </tr>
        </thead>

        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.job_id}
              tabIndex={0}
              className="job-table-row"
              onClick={() => onSelectJob(job)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectJob(job);
                }
              }}
            >
              <td>
                <strong>{getJobShortId(job.job_id)}</strong>
              </td>
              <td>{job.workload_type}</td>
              <td>{formatJobInput(job.input_data)}</td>
              <td>{job.worker_id}</td>
              <td>{formatJobTimestamp(job.created_at)}</td>
              <td>
                <span className={`job-status job-status--${job.status}`}>
                  <span className="job-status-dot" />
                  {getJobStatusLabel(job.status)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}