# Containerized form of this task's environment for real Harbor runs.
# Build context must be the repo root:
#   docker build -f evals/reimport-dedup/environment/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /repo
COPY harness/ harness/
COPY evals/lib/ evals/lib/
COPY evals/personas/ evals/personas/
ENV REPO=/repo \
    WS=/workspace/finance \
    ARTIFACTS=/logs/artifacts \
    REWARD_DIR=/logs/verifier \
    PERSONA=/repo/evals/personas/p01-alex-baseline.md \
    MANIFEST=/repo/evals/fixtures/p01-alex-baseline/manifest.json \
    MONTH=2026-06
COPY evals/reimport-dedup/environment/setup.sh /setup.sh
RUN mkdir -p /workspace /logs/artifacts /logs/verifier && bash /setup.sh
