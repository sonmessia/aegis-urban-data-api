# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder
# Uses the official Rust image so we get cargo, rustc, and system libs out-of-box.
# We layer the dependency build separately from source to leverage Docker cache:
#   - If only src/ changes → only the final `cargo build` layer re-runs.
#   - If Cargo.toml/Cargo.lock change → dependency layer also re-runs.
# ──────────────────────────────────────────────────────────────────────────────
FROM rust:1.75-slim AS builder

# Install system libraries required at compile time
#   libssl-dev  → required by sqlx / reqwest (TLS)
#   pkg-config  → helps the Rust build scripts locate system libraries
#   ca-certificates → needed for HTTPS fetches during build (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    pkg-config \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ── Dependency caching trick ──────────────────────────────────────────────────
# 1. Copy only the manifest files.
# 2. Create a dummy src/main.rs so Cargo can compile a valid (but empty) crate.
# 3. Build dependencies with --release so they are cached as a layer.
# 4. Remove the dummy artefacts — they will be rebuilt from real source below.
# This means Docker only re-runs the expensive dep build when Cargo.lock changes,
# not on every source file edit.
COPY Cargo.toml Cargo.lock ./

# If the workspace has member crates, copy their manifests here too.
# Adjust the glob if your workspace layout differs.
# COPY crates/some-lib/Cargo.toml crates/some-lib/Cargo.toml

RUN mkdir -p src \
 && echo 'fn main() {}' > src/main.rs \
 && cargo build --release --locked \
 && rm -rf src target/release/.fingerprint/urban-data-api-*

# ── Build real application ─────────────────────────────────────────────────────
COPY src ./src

RUN cargo build --release --locked

# Strip debug symbols → reduces binary size significantly (often 30–50%)
RUN strip target/release/urban-data-api

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime
# gcr.io/distroless/cc-debian12 provides:
#   - libgcc, libstdc++, glibc (required by most Rust binaries)
#   - No shell, no package manager, no extra attack surface
#   - ~20 MB final image vs ~200 MB for debian:slim
# ──────────────────────────────────────────────────────────────────────────────
FROM gcr.io/distroless/cc-debian12 AS runtime

# Run as non-root — distroless ships with uid 65532 ("nonroot")
USER 65532:65532

WORKDIR /app

# Copy the stripped binary from the builder stage
COPY --from=builder --chown=65532:65532 /build/target/release/urban-data-api /urban-data-api

# Runtime behaviour configuration
ENV RUST_LOG=info
ENV RUST_BACKTRACE=0

# Application port (match your Axum/Actix-web bind address)
EXPOSE 8080

# Distroless images do not have a shell; use the exec form of CMD.
CMD ["/urban-data-api"]
