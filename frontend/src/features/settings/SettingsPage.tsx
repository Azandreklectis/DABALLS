import { useCallback, useEffect, useState } from "react";
import Button from "../../components/ui/Button";
import ErrorMessage from "../../components/ui/ErrorMessage";
import LoadingState from "../../components/ui/LoadingState";
import PageHeader from "../../layout/PageHeader";
import { apiRequest } from "../../api/client";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);

  const checkController = useCallback(async () => {
    setChecking(true);
    setError(null);
    try {
      const result = await apiRequest<HealthResponse>("/health");
      setHealth(result);
      setCheckedAt(new Date().toISOString());
    } catch (err: unknown) {
      setHealth(null);
      setError(err instanceof Error ? err.message : "Controller health check failed.");
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    void checkController();
  }, [checkController]);

  return (
    <section className="page-content">
      <PageHeader
        eyebrow="SYSTEM / CONFIGURATION"
        title="Settings"
        description="Inspect the controller connection and the current frontend runtime configuration."
        actions={
          <Button
            variant="secondary"
            onClick={() => void checkController()}
            loading={checking}
            disabled={checking}
          >
            Check connection
          </Button>
        }
      />

      <section className="settings-panel">
        <div className="settings-panel-heading">
          <div>
            <span className="settings-eyebrow">01 / CONNECTIVITY</span>
            <h2>Controller health</h2>
            <p>Checks whether the API serving this dashboard is reachable.</p>
          </div>
          <span className={`settings-connection-status ${health ? "is-online" : error ? "is-offline" : ""}`}>
            <span />
            {checking ? "Checking" : health ? "Connected" : error ? "Unavailable" : "Unknown"}
          </span>
        </div>

        {checking && !health ? (
          <LoadingState label="Checking controller…" />
        ) : error ? (
          <ErrorMessage
            title="Controller connection failed"
            message={error}
            action={
              <Button variant="secondary" onClick={() => void checkController()}>
                Try again
              </Button>
            }
          />
        ) : health ? (
          <dl className="settings-detail-grid">
            <div><dt>Service</dt><dd>{health.service}</dd></div>
            <div><dt>API status</dt><dd>{health.status}</dd></div>
            <div><dt>Controller version</dt><dd>{health.version}</dd></div>
            <div>
              <dt>Last checked</dt>
              <dd>{checkedAt ? new Date(checkedAt).toLocaleString() : "—"}</dd>
            </div>
          </dl>
        ) : null}
      </section>

      <section className="settings-panel">
        <div className="settings-panel-heading">
          <div>
            <span className="settings-eyebrow">02 / FRONTEND</span>
            <h2>Runtime configuration</h2>
            <p>Current connection and refresh behavior used by the dashboard.</p>
          </div>
        </div>
        <dl className="settings-detail-grid">
          <div><dt>API path</dt><dd><code>/api</code></dd></div>
          <div><dt>Worker refresh</dt><dd>Every 5 seconds</dd></div>
          <div><dt>Job refresh</dt><dd>Every 5 seconds</dd></div>
          <div><dt>Connection mode</dt><dd>Same-origin API proxy</dd></div>
        </dl>
        <p className="settings-note">
          The frontend expects the development server or deployment gateway to proxy
          <code> /api </code> to the DABALLS controller. Change the proxy or deployment
          configuration when the controller is hosted elsewhere; this page does not
          modify server settings.
        </p>
      </section>

      <section className="settings-panel">
        <div className="settings-panel-heading">
          <div>
            <span className="settings-eyebrow">03 / RESOURCE MODEL</span>
            <h2>Resource allocation</h2>
            <p>How the current scheduler interprets worker contributions.</p>
          </div>
        </div>
        <ul className="settings-list">
          <li>Workers advertise CPU cores and memory to the controller.</li>
          <li>Jobs declare minimum CPU and memory requirements for scheduling.</li>
          <li>Advertised capacity guides placement; it does not enforce OS-level resource isolation.</li>
          <li>RAM contributed by separate machines is not combined into one shared memory address space.</li>
        </ul>
      </section>
    </section>
  );
}
