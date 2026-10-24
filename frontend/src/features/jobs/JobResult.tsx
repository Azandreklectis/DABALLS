import type { Job } from "../../types/job";

interface JobResultProps {
  job: Job;
}

export default function JobResult({ job }: JobResultProps) {
  if (job.status === "failed") {
    return (
      <div className="job-result job-result--failed" role="status">
        <span className="job-result-label">EXECUTION FAILED</span>
        <p>{job.error || "The job failed without an error message."}</p>
      </div>
    );
  }

  if (job.status !== "completed") {
    return (
      <div className="job-result job-result--pending" role="status">
        <span className="job-result-label">RESULT UNAVAILABLE</span>
        <p>
          {job.status === "running"
            ? "The worker is still processing this job."
            : "This job is waiting to be executed."}
        </p>
      </div>
    );
  }

  if (job.result_data != null) {
    return (
      <div className="job-result job-result--success" role="status">
        <span className="job-result-label">PACKAGED WORKLOAD RESULT</span>
        <pre className="job-result-json">{JSON.stringify(job.result_data, null, 2)}</pre>
      </div>
    );
  }

  if (job.result === null) {
    return (
      <div className="job-result job-result--pending" role="status">
        <span className="job-result-label">NO RESULT REPORTED</span>
        <p>The job is marked completed, but the controller returned no result.</p>
      </div>
    );
  }

  return (
    <div className="job-result job-result--success" role="status">
      <span className="job-result-label">COMPUTATION RESULT</span>
      <strong>{job.result}</strong>
      <p>{job.workload_type === "sum_integers"
        ? `Sum of ${job.input_data?.length ?? 0} input integers.`
        : "Packaged workload completed successfully."}</p>
    </div>
  );
}
