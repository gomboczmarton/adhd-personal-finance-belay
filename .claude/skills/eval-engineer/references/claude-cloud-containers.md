# Running full Harbor evals in Claude Code cloud containers

Field-verified 2026-07-23 in a Claude Code on the web session (belay harness:
three Harbor tasks at reward 1.0 under `harbor run --env docker`). Everything
below was tested, not assumed.

## What the remote container image already has — and lacks

| Present | Absent |
|---|---|
| `dockerd`, `containerd`, `runc`, `docker` client (root user, overlayfs, cgroups v1) | A **running** Docker daemon (`/var/run/docker.sock` does not exist until something starts `dockerd`) |
| `uv` | The **Harbor CLI** (`uv tool install harbor`) |

Starting `dockerd` just works — no privileged-mode workarounds, no storage-driver
flags, image pulls go through the session proxy. So "install Docker" is the
wrong fix; "start the daemon" is the whole fix.

## Install into the target repo (do this when scaffolding a harness)

1. Copy `assets/session-start.sh` → `<target>/.claude/hooks/session-start.sh`
   (`chmod +x`). It starts the daemon, installs the Harbor CLI (cached in the
   container snapshot after the first session), and adds `~/.local/bin` to the
   session PATH. It is remote-only (`$CLAUDE_CODE_REMOTE`) and resilient —
   failures degrade to the repo's local runner, never block startup.
2. Register it: merge `assets/settings.json` into `<target>/.claude/settings.json`.
3. Copy `assets/prepare_containers.sh` → `<target>/evals/prepare_containers.sh`
   and set its `STAGE_PATHS`. Git-ignore `evals/*/environment/ctx/` and
   `evals/jobs/`.
4. Validate the hook in-session before committing:
   `pkill dockerd; CLAUDE_CODE_REMOTE=true ./.claude/hooks/session-start.sh`
   then `docker run --rm hello-world` and `harbor --version`.
5. Once merged to the default branch, every future cloud session gets
   Docker + Harbor automatically.

## TLS interception (the one real gotcha)

Outbound HTTPS from **inside task containers** is transparently intercepted by
the session proxy — downloads fail certificate verification ("self-signed
certificate in certificate chain") even with no proxy env set. Fix, in this
order of preference:

1. **Need no network**: verifiers and environments that never download at
   build/run time (pre-staged fixtures, pre-installed interpreters). Best eval
   hygiene regardless of environment.
2. **Trust the CA**: `prepare_containers.sh` stages `/root/.ccr/ca-bundle.crt`
   into each build context; the task Dockerfile appends it to the system trust
   store and sets `SSL_CERT_FILE`:

   ```dockerfile
   COPY ctx/ca-bundle.crt /usr/local/share/ca-certificates/session-proxy.crt
   ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
   RUN cat /usr/local/share/ca-certificates/session-proxy.crt >> /etc/ssl/certs/ca-certificates.crt
   ```

Never disable TLS verification, and never bake the CA file into a committed
image or push it to a registry — it is session infrastructure, staged fresh
per run into a git-ignored `ctx/`.

## Harbor 0.20 task gotchas (cost an hour; don't re-pay it)

- **Validation failures are silent.** A task that fails `task.toml` validation
  simply disappears from discovery ("0 tasks available"), with no error. Debug
  by validating directly:
  `<harbor-venv>/bin/python -c "from harbor.models.task.config import TaskConfig; TaskConfig.model_validate_toml(open('task.toml').read())"`
- Required shape: `schema_version = "1.3"` at top; `[task] name = "org/name"`
  (org-qualified); `authors = [{ name = "..." }]` (Author objects, not
  strings). Custom fields under `[metadata]` are fine.
- **Build context is `environment/`, not the repo root.** Everything the image
  needs must be staged inside it — hence `prepare_containers.sh`.
- Harbor copies `tests/` → `/tests` and `solution/` → `/solution` into the
  container **at runtime**; scripts inside `tests/` must resolve siblings via
  `$(dirname "${BASH_SOURCE[0]}")`, not repo paths baked into the image.
- The `oracle` agent runs `solution/solve.sh` — a full infrastructure check
  (build → agent → verifier → reward) with no model cost. Run it before any
  real-agent run.
- The scaffold's default `tests/test.sh` downloads `uv` at verify time — it
  hits the TLS wall above. Replace it with a network-free verifier.

## Degradation path

Docker unavailable (hook prints the warning) → the repo's local runner
(`evals/run_local.py` pattern: same setup/solve/test phases, same `reward.txt`
contract, same infrastructure-error vs reward-0 distinction) keeps the suite
gating changes. Tasks stay Harbor-portable because the format never forked.
