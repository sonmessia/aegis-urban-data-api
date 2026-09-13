# ─── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv — ultra-fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (layer cache: only re-runs if deps change)
COPY pyproject.toml uv.lock* ./

# Install dependencies into /app/.venv (no system site-packages pollution)
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source
COPY app/ ./app/
COPY main.py ./

# Install the project itself (editable not needed in final image)
RUN uv sync --frozen --no-dev


# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --no-create-home appuser

WORKDIR /app

# Copy only the virtualenv and app from builder — no build tools in final image
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/app /app/app
COPY --from=builder --chown=appuser:appgroup /app/main.py /app/main.py

# Activate venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

USER appuser

EXPOSE 8080

# Uvicorn with 1 worker (scale horizontally via Kubernetes replicas)
CMD ["uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "--no-access-log"]
