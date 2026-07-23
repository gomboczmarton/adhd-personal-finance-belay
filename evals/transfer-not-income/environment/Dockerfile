# Self-contained task environment for real Harbor runs.
# Run `bash evals/prepare_containers.sh` first — it stages ctx/ (harness,
# eval lib, personas, fixtures, and the session-proxy CA bundle when present).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
COPY ctx/ca-bundle.crt /usr/local/share/ca-certificates/session-proxy.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
RUN cat /usr/local/share/ca-certificates/session-proxy.crt >> /etc/ssl/certs/ca-certificates.crt
WORKDIR /repo
COPY ctx/harness/ harness/
COPY ctx/evals/ evals/
ENV REPO=/repo \
    WS=/workspace/finance \
    ARTIFACTS=/logs/artifacts \
    REWARD_DIR=/logs/verifier \
    PERSONA=/repo/evals/personas/p02-kim-hidden-transfers.md \
    MANIFEST=/repo/evals/fixtures/p02-kim-hidden-transfers/manifest.json \
    MONTH=2026-06
RUN mkdir -p /workspace /logs/artifacts /logs/verifier /logs/agent \
    && bash evals/transfer-not-income/environment/setup.sh
