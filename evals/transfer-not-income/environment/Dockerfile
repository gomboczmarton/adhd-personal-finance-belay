# Containerized form of this task's environment for real Harbor runs.
# Build context must be the repo root:
#   docker build -f evals/transfer-not-income/environment/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /repo
COPY harness/ harness/
COPY evals/lib/ evals/lib/
COPY evals/personas/ evals/personas/
ENV REPO=/repo \
    WS=/workspace/finance \
    ARTIFACTS=/logs/artifacts \
    REWARD_DIR=/logs/verifier \
    PERSONA=/repo/evals/personas/p02-kim-hidden-transfers.md \
    MANIFEST=/repo/evals/fixtures/p02-kim-hidden-transfers/manifest.json \
    MONTH=2026-06
COPY evals/transfer-not-income/environment/setup.sh /setup.sh
RUN mkdir -p /workspace /logs/artifacts /logs/verifier && bash /setup.sh
