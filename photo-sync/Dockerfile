# Template Dockerfile for a fleet app. Copied in by fleet/bin/new-app.sh.
#
# Conventions (see fleet/AGENTS.md):
#   * uv manages Python and dependencies; uv.lock is committed and frozen.
#   * The image is built in GitHub Actions and pushed to GHCR. The Mac only pulls.
#   * The container is long-running: loop.py calls the app's main() on an
#     interval. Docker's restart policy handles crashes; there is no cron.
#   * Non-root user; the app owns /app so it can write there if it must, but
#     nothing it writes survives a container replace. State belongs elsewhere.

# Pin the minor. Bump deliberately, when already touching the repo.
FROM python:3.12-slim

# uv from its official image: reproducible, no curl|sh.
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first so this layer caches across code-only changes. With
# [tool.uv] package = false the project itself is never installed, so this
# single sync is the whole environment; the code just needs to be present.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Then the code.
COPY . .

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

ENV PATH="/app/.venv/bin:$PATH"

# loop.py: run main() every $LOOP_INTERVAL seconds, forever.
CMD ["python", "loop.py"]
