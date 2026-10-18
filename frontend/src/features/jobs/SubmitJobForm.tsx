
import { useState, type FormEvent } from "react";
import type { Worker } from "../../types/worker";
import type { Job, JobSubmission } from "../../types/job";
import Button from "../../components/ui/Button";

interface SubmitJobFormProps {
  workers: Worker[];
  submitting: boolean;
  onSubmit: (submission: JobSubmission) => Promise<Job>;
}

export default function SubmitJobForm({
  workers,
  submitting,
  onSubmit,
}: SubmitJobFormProps) {
  const [workerId, setWorkerId] = useState("");
  const [inputText, setInputText] = useState("1, 2, 3, 4, 5");
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (!workerId) {
      setFormError("Select a worker before submitting the job.");
      return;
    }

    const tokens = inputText.split(",").map((value) => value.trim());

    if (
      tokens.length === 0 ||
      tokens.length > 10000 ||
      tokens.some((token) => token === "" || !/^-?\d+$/.test(token))
    ) {
      setFormError("Enter between 1 and 10,000 comma-separated integers.");
      return;
    }

    const inputData = tokens.map(Number);

    if (inputData.some((value) => !Number.isSafeInteger(value))) {
      setFormError("Each input must be a safe integer.");
      return;
    }

    const submission: JobSubmission = {
      worker_id: workerId,
      workload_type: "sum_integers",
      input_data: inputData,
    };

    try {
      const job = await onSubmit(submission);
      setSuccessMessage(`Job submitted successfully: ${job.job_id}`);
    } catch (err: unknown) {
      setFormError(
        err instanceof Error ? err.message : "Job submission failed.",
      );
    }
  }

  const onlineWorkers = workers.filter(
    (worker) => worker.status === "online",
  );

  return (
    <form className="submit-job-form" onSubmit={handleSubmit}>
      <div className="submit-job-heading">
        <div>
          <span className="job-form-eyebrow">NEW WORKLOAD</span>
          <h2>Submit a job</h2>
          <p>Calculate the sum of an integer list on a selected worker.</p>
        </div>
      </div>

      <label htmlFor="job-worker">Target worker</label>
      <select
        id="job-worker"
        value={workerId}
        onChange={(event) => setWorkerId(event.target.value)}
        disabled={submitting || onlineWorkers.length === 0}
        required
      >
        <option value="">Select an online worker</option>
        {onlineWorkers.map((worker) => (
          <option key={worker.worker_id} value={worker.worker_id}>
            {worker.hostname} ({worker.cpu_logical_cores} CPU cores)
          </option>
        ))}
      </select>

      {onlineWorkers.length === 0 && (
        <p className="job-form-hint">
          No online workers are available. Start and register a worker first.
        </p>
      )}

      <label htmlFor="job-input">Integer input</label>
      <textarea
        id="job-input"
        value={inputText}
        onChange={(event) => setInputText(event.target.value)}
        placeholder="Example: 10, 20, 30, 40"
        rows={3}
        disabled={submitting}
        required
      />

      <p className="job-form-hint">
        Use commas between integers. Maximum 10,000 values.
      </p>

      {formError && (
        <p className="job-form-message job-form-message--error" role="alert">
          {formError}
        </p>
      )}

      {successMessage && (
        <p className="job-form-message job-form-message--success" role="status">
          {successMessage}
        </p>
      )}

      <Button
        type="submit"
        variant="primary"
        loading={submitting}
        disabled={submitting || onlineWorkers.length === 0}
      >
        Submit job
      </Button>
    </form>
  );
}