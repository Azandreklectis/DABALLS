import { useState, type FormEvent } from "react";
import type { Worker } from "../../types/worker";
import type { Job, JobSubmission } from "../../types/job";
import { uploadArtifact } from "../../api/artifacts";
import Button from "../../components/ui/Button";

interface SubmitJobFormProps {
  workers: Worker[];
  submitting: boolean;
  onSubmit: (submission: JobSubmission) => Promise<Job>;
}

const DEFAULT_MEMORY_MIB = "512";
const MAX_MEMORY_MIB = 1024 * 1024;

export default function SubmitJobForm({
  workers,
  submitting,
  onSubmit,
}: SubmitJobFormProps) {
  const [workerId, setWorkerId] = useState("");
  const [workloadType, setWorkloadType] = useState<"sum_integers" | "python_package">("sum_integers");
  const [inputText, setInputText] = useState("1, 2, 3, 4, 5");
  const [packageFile, setPackageFile] = useState<File | null>(null);
  const [cpuCores, setCpuCores] = useState("1");
  const [memoryMiB, setMemoryMiB] = useState(DEFAULT_MEMORY_MIB);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const busy = submitting || uploading;
  const onlineWorkers = workers.filter((worker) => worker.status === "online");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const requiredCpu = Number(cpuCores);
    const requiredMemoryMiB = Number(memoryMiB);

    if (!Number.isSafeInteger(requiredCpu) || requiredCpu < 1 || requiredCpu > 4096) {
      setFormError("CPU requirements must be a whole number from 1 to 4096.");
      return;
    }

    if (
      !Number.isSafeInteger(requiredMemoryMiB) ||
      requiredMemoryMiB < 1 ||
      requiredMemoryMiB > MAX_MEMORY_MIB
    ) {
      setFormError("Memory must be a whole number of MiB, up to 1,048,576 MiB.");
      return;
    }

    const common = {
      ...(workerId ? { worker_id: workerId } : {}),
      required_cpu_cores: requiredCpu,
      required_memory_bytes: requiredMemoryMiB * 1024 * 1024,
    };

    try {
      let submission: JobSubmission;

      if (workloadType === "python_package") {
        if (!packageFile) {
          setFormError("Choose a ZIP workload package before submitting.");
          return;
        }

        setUploading(true);
        const artifact = await uploadArtifact(packageFile);
        setUploading(false);

        submission = {
          ...common,
          workload_type: "python_package",
          artifact_id: artifact.artifact_id,
        };
      } else {
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

        submission = {
          ...common,
          workload_type: "sum_integers",
          input_data: inputData,
        };
      }

      const job = await onSubmit(submission);
      const assignedWorker = workers.find((worker) => worker.worker_id === job.worker_id);
      const workerLabel = assignedWorker
        ? assignedWorker.display_name || assignedWorker.hostname
        : job.worker_id;

      setSuccessMessage(`Job queued: ${job.job_id}. Assigned worker: ${workerLabel}.`);
      if (workloadType === "python_package") setPackageFile(null);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Job submission failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <form className="submit-job-form" onSubmit={handleSubmit}>
      <div className="submit-job-heading">
        <div>
          <span className="job-form-eyebrow">NEW WORKLOAD</span>
          <h2>Submit a job</h2>
          <p>Submit a computation or a packaged Python workload to your cluster.</p>
        </div>
      </div>

      <label htmlFor="job-workload-type">Workload type</label>
      <select
        id="job-workload-type"
        value={workloadType}
        onChange={(event) => setWorkloadType(event.target.value as typeof workloadType)}
        disabled={busy}
      >
        <option value="sum_integers">Sum integers</option>
        <option value="python_package">Packaged Python workload (ZIP)</option>
      </select>

      <label htmlFor="job-worker">Worker assignment</label>
      <select
        id="job-worker"
        value={workerId}
        onChange={(event) => setWorkerId(event.target.value)}
        disabled={busy}
      >
        <option value="">Automatic scheduling</option>
        {onlineWorkers.map((worker) => (
          <option key={worker.worker_id} value={worker.worker_id}>
            {worker.display_name || worker.hostname} — {worker.offered_cpu_cores} offered CPU cores,{" "}
            {(worker.offered_memory_bytes / 1024 ** 3).toFixed(2)} GiB offered RAM
          </option>
        ))}
      </select>

      <p className="job-form-hint">
        Automatic scheduling selects an online worker with enough unallocated advertised capacity.
      </p>

      {workloadType === "sum_integers" ? (
        <>
          <label htmlFor="job-input">Integer input</label>
          <textarea
            id="job-input"
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            placeholder="Example: 10, 20, 30, 40"
            rows={3}
            disabled={busy}
            required
          />
          <p className="job-form-hint">Use commas between integers. Maximum 10,000 values.</p>
        </>
      ) : (
        <div className="job-package-upload">
          <label htmlFor="job-package">Workload ZIP package</label>
          <input
            id="job-package"
            type="file"
            accept=".zip,application/zip"
            onChange={(event) => setPackageFile(event.target.files?.[0] ?? null)}
            disabled={busy}
          />
          {packageFile && (
            <p className="job-form-hint">
              Selected: {packageFile.name} ({(packageFile.size / 1024 ** 2).toFixed(2)} MiB)
            </p>
          )}
          <p className="job-form-hint">
            ZIP must contain manifest.json, main.py, input.json and requirements.txt.
            The manifest must use format_version 1. The entrypoint reads its declared input
            file and writes the declared output file.
          </p>
          <p className="job-form-hint">
            Upload limit: 50 MiB. Only submit code and dependencies you trust.
          </p>
        </div>
      )}

      <div className="job-resource-fields">
        <div>
          <label htmlFor="job-cpu">Required CPU cores</label>
          <input
            id="job-cpu"
            type="number"
            min="1"
            max="4096"
            step="1"
            value={cpuCores}
            onChange={(event) => setCpuCores(event.target.value)}
            disabled={busy}
            required
          />
        </div>
        <div>
          <label htmlFor="job-memory">Required memory (MiB)</label>
          <input
            id="job-memory"
            type="number"
            min="1"
            max={MAX_MEMORY_MIB}
            step="1"
            value={memoryMiB}
            onChange={(event) => setMemoryMiB(event.target.value)}
            disabled={busy}
            required
          />
        </div>
      </div>

      <p className="job-form-hint">
        Defaults: 1 CPU core and 512 MiB. These are scheduler capacity estimates, not physical
        RAM reservations or CPU isolation.
      </p>

      {formError && (
        <p className="job-form-message job-form-message--error" role="alert">{formError}</p>
      )}
      {successMessage && (
        <p className="job-form-message job-form-message--success" role="status">{successMessage}</p>
      )}

      <Button type="submit" variant="primary" loading={busy} disabled={busy}>
        {uploading ? "Uploading package…" : submitting ? "Submitting job…" : "Submit job"}
      </Button>
    </form>
  );
}
