

## Local development and deployment

### Requirements

- Python 3.12 or newer
- Node.js and npm for the React frontend
- WSL/Linux or another supported Python environment

### Install dependencies

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

### Configure the controller

Copy `.env.example` to `.env` as a reference. The application does not automatically load `.env`; export the variables in your shell or configure them in your process manager.

For local development, the API token can remain unset. For a controller reachable by other machines, configure a strong token before starting it:

```bash
export DABALLS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DABALLS_DATABASE_PATH="$HOME/.daballs/controller.sqlite3"
export DABALLS_ARTIFACT_DIR="$HOME/.daballs/artifacts"
export DABALLS_JOB_RUNTIME_DIR="$HOME/.daballs/job-runtime"
```

Keep the token private. Every worker connecting to this controller must receive the same `DABALLS_API_TOKEN` in its environment.

### Start the controller

From the repository root, with the virtual environment activated:

```bash
uvicorn daballs.controller.main:app --host 127.0.0.1 --port 8000
```

Use `--host 0.0.0.0` only when remote machines need to connect, and protect the service with authentication and appropriate network controls. Use HTTPS/TLS for traffic across untrusted networks.

### Start a worker

In a second terminal, activate the same project environment and export the same token if one is configured:

```bash
cd ~/projects/daballs
source .venv/bin/activate
export DABALLS_API_TOKEN="your-controller-token"
```

Then start the worker using the entry point or instructions defined by the current worker-agent implementation. Worker IDs and contribution settings should be configured according to the worker registration interface.

### Start the frontend

In a third terminal:

```bash
cd ~/projects/daballs/frontend
npm install
npm run dev
```

The Vite development server uses the project's configured API proxy. If the controller requires a token, copy `frontend/.env.example` to `frontend/.env.local`, set `VITE_DABALLS_API_TOKEN` to the same token for a local demonstration, and restart Vite.

**Frontend token warning:** Vite variables prefixed with `VITE_` are bundled into browser JavaScript and can be read by users. This is only suitable for a trusted local demonstration. For a public deployment, use a server-side proxy or implement proper user authentication instead of distributing a shared secret to browsers.

### Run the local multi-worker demonstration

From the repository root:

```bash
python scripts/demo_local_cluster.py
```

This demonstrates multiple worker processes on one machine. It does not prove execution across separate physical computers.

### Run checks

```bash
.venv/bin/ruff check .
.venv/bin/pytest -q
cd frontend && npm run build
```

### Security and current limitations

- Configure `DABALLS_API_TOKEN` for API authentication whenever the controller is exposed beyond a trusted local development environment.
- The health endpoint is intentionally available without the API token.
- Python workload execution currently uses a virtual environment, not a security-grade OS sandbox. Execute only trusted workload packages.
- A shared bearer token is not a substitute for per-user identities, authorization policies, TLS, rate limiting, or OS-level workload isolation.
- SQLite and the artifact directory must be stored on persistent storage and included in the deployment's backup plan.


## Docker Compose deployment

Docker Compose runs one controller and two worker containers. The workers are separate containers, not separate physical machines.

1. Install Docker Engine and the Docker Compose plugin.
2. Create a root `.env` file with a strong random token:

   ```bash
   cp .env.example .env
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

   Put the generated token after `DABALLS_API_TOKEN=` in `.env`. Do not commit or share this file.
3. Start the stack:

   ```bash
   docker compose --env-file .env up --build -d
   ```
4. Check the controller and worker logs:

   ```bash
   docker compose --env-file .env ps
   docker compose --env-file .env logs --tail=100 controller worker-a worker-b
   ```
5. The controller API is published on port 8000. For example, query the workers from the host:

   ```bash
   TOKEN="$(sed -n 's/^DABALLS_API_TOKEN=//p' .env)"
   curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/v1/workers
   ```
6. Stop the stack with `docker compose --env-file .env down`. The named `daballs-data` volume is retained unless explicitly removed.

The Compose file is a starting point for a trusted demonstration, not a production security boundary. It does not configure TLS, resource limits, a reverse proxy, per-user authorization, or OS-level workload sandboxing. Do not expose the controller directly to the public internet. The frontend is not served by this Compose stack; use the documented Vite development server for the UI demonstration.
