import { useMemo, useState } from "react";
import PageHeader from "../../layout/PageHeader";
import { Link } from "react-router-dom";

function shellQuote(value: string): string {
  return "'" + value.replace(/'/g, "'\\''") + "'";
}

export default function WorkerRegistrationPage() {
  const [displayName, setDisplayName] = useState("");
  const [cpuCores, setCpuCores] = useState("0");
  const [memoryGiB, setMemoryGiB] = useState("2");
  const [controllerUrl, setControllerUrl] =
    useState("http://127.0.0.1:8000");
  const [copied, setCopied] = useState(false);

  const cpu = Number(cpuCores);
  const memory = Number(memoryGiB);

  const valid =
    displayName.trim().length > 0 &&
    displayName.trim().length <= 100 &&
    Number.isInteger(cpu) &&
    cpu >= 0 &&
    cpu <= 4096 &&
    Number.isFinite(memory) &&
    memory >= 0 &&
    memory <= 1048576 &&
    Number.isInteger(memory * 1024) &&
    /^https?:\/\/[^ ]+$/.test(controllerUrl.trim());

  const command = useMemo(() => {
    const name = displayName.trim() || "My DABALLS Worker";
    const url = controllerUrl.trim();

    return [
      "cd ~/projects/daballs",
      "source .venv/bin/activate",
      "python -m daballs.worker.agent \\",
      `  --display-name ${shellQuote(name)} \\`,
      `  --controller-url ${shellQuote(url)} \\`,
      `  --offer-cpu-cores ${cpu} \\`,
      `  --offer-memory-mib ${Math.round(memory * 1024)}`,
    ].join("\n");
  }, [displayName, controllerUrl, cpu, memory]);

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="page-content">
      <PageHeader
        eyebrow="WORKERS / ONBOARDING"
        title="Join the network"
        description="Configure a computer to contribute resources to DABALLS. Review the offer, launch the worker agent, and confirm registration."
      />

      <div className="onboarding-layout">
        <div className="onboarding-main">
          <section className="onboarding-panel">
            <div className="onboarding-section-heading">
              <span className="onboarding-step">01</span>
              <div>
                <h2>Identify this machine</h2>
                <p>Give your computer a recognizable name.</p>
              </div>
            </div>

            <label className="onboarding-field">
              <span>Worker display name</span>
              <input
                value={displayName}
                maxLength={100}
                placeholder="e.g. Tushar's Laptop"
                onChange={(event) => setDisplayName(event.target.value)}
              />
              <small>
                This label helps distinguish the machine in the Workers page.
                Its stable worker ID remains separate.
              </small>
            </label>

            <label className="onboarding-field">
              <span>Controller URL</span>
              <input
                value={controllerUrl}
                onChange={(event) => setControllerUrl(event.target.value)}
                placeholder="http://127.0.0.1:8000"
                spellCheck={false}
              />
              <small>
                Use 127.0.0.1 only when the worker and controller share the
                same network namespace. For another computer, use the
                controller's reachable address.
              </small>
            </label>
          </section>

          <section className="onboarding-panel">
            <div className="onboarding-section-heading">
              <span className="onboarding-step">02</span>
              <div>
                <h2>Choose your contribution</h2>
                <p>Configure the resources the agent will advertise.</p>
              </div>
            </div>

            <label className="onboarding-field">
              <span>CPU cores offered</span>
              <input
                type="number"
                min="0"
                max="4096"
                step="1"
                value={cpuCores}
                onChange={(event) => setCpuCores(event.target.value)}
              />
              <small>
                Enter the number of logical CPU cores you want to offer.
                The agent and controller validate the offer against detected
                machine resources.
              </small>
            </label>

            <label className="onboarding-field">
              <span>RAM offered (GiB)</span>
              <input
                type="number"
                min="0"
                max="1024"
                step="0.25"
                value={memoryGiB}
                onChange={(event) => setMemoryGiB(event.target.value)}
              />
              <small>
                The value is converted to MiB for the agent. The selected
                amount is an advertised offer, not a memory reservation.
              </small>
            </label>

            <div className="onboarding-resource-summary">
              <div>
                <span>CPU contribution</span>
                <strong>{valid ? `${cpu} cores` : "Check values"}</strong>
              </div>
              <div>
                <span>RAM contribution</span>
                <strong>
                  {valid ? `${memory.toLocaleString()} GiB` : "Check values"}
                </strong>
              </div>
            </div>
          </section>

          <section className="onboarding-panel">
            <div className="onboarding-section-heading">
              <span className="onboarding-step">03</span>
              <div>
                <h2>Launch the worker</h2>
                <p>
                  Run this command in the terminal of the computer you want
                  to contribute.
                </p>
              </div>
            </div>

            {!valid && (
              <p className="onboarding-validation" role="alert">
                Enter a valid name, controller URL, and non-negative resource
                offers before copying the command.
              </p>
            )}

            <pre className="onboarding-command">
              <code>{command}</code>
            </pre>

            <div className="onboarding-actions">
              <button
                className="button button--primary button--medium"
                type="button"
                disabled={!valid}
                onClick={() => void copyCommand()}
              >
                {copied ? "Command copied" : "Copy launch command"}
              </button>

              <Link className="button button--secondary button--medium" to="/workers">
                View workers
              </Link>
            </div>

            <p className="onboarding-note">
              Registration happens when the Python agent runs successfully.
              Keep that terminal open to maintain heartbeats and process jobs.
              Hardware details will appear in the Workers page after
              registration.
            </p>
          </section>
        </div>

        <aside className="onboarding-aside">
          <p className="onboarding-aside-label">BEFORE YOU JOIN</p>
          <h2>Resources, on your terms.</h2>
          <p>
            DABALLS records the resource offer and the hardware information
            reported by the worker agent.
          </p>
          <ul>
            <li>Use a stable worker identity.</li>
            <li>Choose an offer within the machine's actual capacity.</li>
            <li>Keep the agent running while the machine participates.</li>
          </ul>
          <div className="onboarding-aside-rule" />
          <p>
            This setup advertises resources to the controller. It does not
            guarantee CPU isolation, reserve physical RAM, or combine RAM
            across computers into one shared address space.
          </p>
        </aside>
      </div>
    </section>
  );
}