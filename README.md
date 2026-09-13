# aegis-urban-data-api

[![CI](https://github.com/your-org/aegis-urban-data-api/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/aegis-urban-data-api/actions/workflows/ci.yml)
[![Rust Edition](https://img.shields.io/badge/rust-2021_edition-orange?logo=rust)](https://doc.rust-lang.org/edition-guide/rust-2021/)
[![Docker Image Size](https://img.shields.io/docker/image-size/your-org/aegis-urban-data-api/latest?label=image%20size)](https://gallery.ecr.aws/your-org/aegis-urban-data-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Benchmark workload for the [Aegis Platform](https://github.com/your-org/aegis-infra)** — a production-grade DevSecOps / GitOps platform built as a HUTECH University VJIT Capstone project.

---

## Overview

`aegis-urban-data-api` is a lightweight **Rust** REST API that simulates IoT urban data ingestion following [FIWARE NGSI-v2](https://fiware-orion.readthedocs.io/en/master/user/ngsiv2_implementation_notes/) conventions. It acts as the primary **benchmark workload** running on the Aegis Platform, exercising the full Kubernetes HA stack — from progressive delivery (Argo Rollouts canary) to database failover (CloudNativePG) and autoscaling (HPA/KEDA).

### What It Simulates

The service models a city's IoT data pipeline, accepting sensor readings from devices (traffic sensors, environmental monitors, smart meters) and persisting them to a PostgreSQL backend. Entity IDs and types follow the NGSI-v2 schema (`urn:ngsi-ld:<Type>:<id>`), making the API realistic enough to benchmark Kubernetes HA behaviour without requiring a full FIWARE Orion deployment.

### Role in the Aegis Platform

| Concern                         | Mechanism                                             |
| ------------------------------- | ----------------------------------------------------- |
| Benchmark under fault injection | Chaos Mesh / AWS FIS target                           |
| Progressive delivery subject    | Argo Rollouts canary analysis                         |
| DB HA demonstration             | CloudNativePG leader election observed via write path |
| Autoscaling trigger             | HPA on CPU + KEDA on queue depth                      |
| Supply-chain security           | `cargo audit` + Trivy in CI                           |

---

## API Endpoints

| Method | Path                | Description                                           | Auth |
| ------ | ------------------- | ----------------------------------------------------- | ---- |
| `POST` | `/v1/entities`      | Ingest IoT sensor entity (NGSI-v2 body)               | —    |
| `GET`  | `/v1/entities/{id}` | Retrieve a single entity by NGSI-v2 ID                | —    |
| `GET`  | `/health`           | Liveness probe — returns `200 OK` if process is alive | None |
| `GET`  | `/ready`            | Readiness probe — checks live PostgreSQL connection   | None |

### Example: Ingest an entity

```bash
curl -X POST http://localhost:8080/v1/entities \
  -H "Content-Type: application/json" \
  -d '{
    "id": "urn:ngsi-ld:TrafficSensor:001",
    "type": "TrafficSensor",
    "speed": { "type": "Number", "value": 42.5 },
    "location": { "type": "geo:point", "value": "10.762622,106.660172" }
  }'
```

### Example: Retrieve an entity

```bash
curl http://localhost:8080/v1/entities/urn:ngsi-ld:TrafficSensor:001
```

### Health / Readiness

```bash
# Liveness (always returns 200 if process is up)
curl http://localhost:8080/health
# {"status":"ok"}

# Readiness (checks PostgreSQL connection pool)
curl http://localhost:8080/ready
# {"status":"ready","db":"connected"}   <- healthy
# {"status":"not_ready","db":"error"}   <- DB unreachable → pod removed from Service
```

> [!IMPORTANT]
> The `/ready` endpoint is intentionally separate from `/health`. During a CloudNativePG leader election failover, pods whose DB connection is lost will fail `/ready` and be removed from the load-balancer endpoints — this is the observable HA event used to measure MTTR.

---

## Why Rust?

Choosing Rust over Go, Python, or Node.js directly impacts the platform's MTTR (Mean Time To Recovery) metric.

| Property             | Rust (this service)     | Go         | Python/FastAPI    |
| -------------------- | ----------------------- | ---------- | ----------------- |
| **Startup time**     | ~5 ms                   | ~30 ms     | ~500 ms           |
| **Binary size**      | < 10 MB                 | ~15 MB     | N/A (interpreter) |
| **Container image**  | < 20 MB (distroless)    | ~30 MB     | ~200 MB           |
| **Memory footprint** | < 20 MB idle            | ~30 MB     | ~80 MB            |
| **Memory safety**    | Compile-time guaranteed | GC-managed | Runtime           |
| **MTTR impact**      | Pod starts in < 1s      | ~1–2s      | 3–5s              |

### MTTR Implication

When a pod is killed (either by Chaos Mesh node failure or Argo Rollouts canary abort), Kubernetes must schedule a replacement. With a 5 ms startup time, the Rust binary is serving traffic again within **under 1 second** of the pod reaching `Running` state. This minimises the MTTR window measured in the HA Validation Tier experiments.

```
[Pod scheduled] → [Image pull (cached)] → [Container start: ~5ms] → [/ready OK] → [Traffic restored]
        ↑                                                                                     ↑
        t=0                                                                              t < 1s
```

### Supply-Chain Security

Rust's ownership model eliminates entire classes of memory vulnerabilities (buffer overflows, use-after-free, data races) at compile time. Combined with `cargo audit` for dependency CVE scanning and `cargo deny` for license policy, the supply chain attack surface is minimal compared to interpreted-language ecosystems.

---

## Local Development

### Prerequisites

| Tool           | Version | Notes                                   |
| -------------- | ------- | --------------------------------------- |
| Rust toolchain | 1.75+   | Install via [rustup](https://rustup.rs) |
| Docker         | 24+     | For container build and local Compose   |
| PostgreSQL     | 15+     | Or use CloudNativePG via k3d cluster    |
| `cargo-audit`  | latest  | `cargo install cargo-audit`             |
| `cargo-watch`  | latest  | Optional: `cargo install cargo-watch`   |

### Clone and Build

```bash
git clone https://github.com/your-org/aegis-urban-data-api.git
cd aegis-urban-data-api

# Debug build (fast iteration)
cargo build

# Release build (production binary)
cargo build --release
```

### Run Tests

```bash
# Unit + integration tests
cargo test

# With output (useful for CI debugging)
cargo test -- --nocapture

# Watch mode for TDD
cargo watch -x test
```

### Lint and Format

```bash
# Static analysis — treat warnings as errors in CI
cargo clippy -- -D warnings

# Code formatting
cargo fmt

# Check formatting without modifying files (CI mode)
cargo fmt -- --check
```

### Run Locally

```bash
# Set required environment variables
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/urban_data"
export RUST_LOG="info"
export APP_PORT="8080"

cargo run
```

### Environment Variables Reference

| Variable                      | Required | Default          | Description                                                      |
| ----------------------------- | -------- | ---------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`                | ✅       | —                | PostgreSQL connection string                                     |
| `APP_PORT`                    | ❌       | `8080`           | HTTP listen port                                                 |
| `RUST_LOG`                    | ❌       | `info`           | Log level (`trace`, `debug`, `info`, `warn`, `error`)            |
| `SECRETS_MANAGER_ENDPOINT`    | ❌       | AWS default      | Override for Floci local emulator (e.g. `http://localhost:4566`) |
| `AWS_REGION`                  | ❌       | `us-east-1`      | AWS region for Secrets Manager lookups                           |
| `AWS_ACCESS_KEY_ID`           | ❌       | —                | AWS credentials (auto-injected via IRSA in Kubernetes)           |
| `AWS_SECRET_ACCESS_KEY`       | ❌       | —                | AWS credentials (auto-injected via IRSA in Kubernetes)           |
| `DB_SECRET_ARN`               | ❌       | —                | ARN of Secrets Manager secret containing DB credentials          |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ❌       | —                | OpenTelemetry Collector endpoint for traces/metrics              |
| `OTEL_SERVICE_NAME`           | ❌       | `urban-data-api` | Service name reported to observability stack                     |

> [!NOTE]
> In Kubernetes, `DATABASE_URL` is **not** set directly. Instead, the External Secrets Operator fetches credentials from AWS Secrets Manager (or Floci locally) and projects them as a Kubernetes `Secret`. The application reads `DB_SECRET_ARN` and resolves the connection string at startup.

---

## Docker Build

### Multi-Stage Build

The `Dockerfile` uses a two-stage build to produce a minimal final image:

```
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│  Stage 1: builder               │       │  Stage 2: runtime                │
│  image: rust:1.75-slim-bookworm │──────▶│  image: gcr.io/distroless/cc     │
│                                 │ COPY  │                                  │
│  • cargo build --release        │ bin   │  • No shell, no package manager  │
│  • Produces: target/release/api │       │  • Binary only → <20 MB image    │
│  • sccache layer cached in CI   │       │  • Non-root user (UID 65532)     │
└─────────────────────────────────┘       └──────────────────────────────────┘
```

The `distroless/cc` base provides only the C runtime (`libc`) needed by Rust binaries — no shell, no `apt`, no attack surface beyond the application itself.

### Build Locally

```bash
# Build the image
docker build -t aegis-urban-data-api:local .

# Run with local PostgreSQL
docker run --rm \
  -e DATABASE_URL="postgres://postgres:postgres@host.docker.internal:5432/urban_data" \
  -e RUST_LOG=info \
  -p 8080:8080 \
  aegis-urban-data-api:local

# Inspect final image size
docker image inspect aegis-urban-data-api:local --format='{{.Size}}' | numfmt --to=iec
```

### ECR Push (CI Managed)

In CI, images are tagged with the Git SHA and pushed to:

| Environment          | Registry                                                          |
| -------------------- | ----------------------------------------------------------------- |
| Dev (local)          | `localhost:4566/aegis-urban-data-api` (Floci ECR mirror)           |
| Demo / HA Validation | `<account-id>.dkr.ecr.<region>.amazonaws.com/aegis-urban-data-api` |

After a successful push, the CI pipeline opens a pull request (or direct commit) to `aegis-infra`, updating the image tag in the Helm values file — triggering Argo CD to reconcile and Argo Rollouts to execute the canary promotion.

---

## CI/CD Pipeline

Every push to `main` or pull request triggers the following GitHub Actions workflow:

```mermaid
flowchart TD
    A([Push to main / PR]) --> B

    subgraph Quality["Quality Gate (parallel)"]
        B[cargo test]
        C[cargo clippy]
        D[cargo fmt --check]
    end

    subgraph Security["Security Scanning (parallel)"]
        E["cargo audit\nSCA — CVEs in deps"]
        F["Semgrep SAST\ncustom Rust rules"]
    end

    B & C & D --> Security
    E & F --> G["Build Docker image\nmulti-stage"]
    G --> H["Trivy image scan\nCRITICAL/HIGH = fail"]
    H --> I{Branch?}
    I -- main --> J["Push to ECR\ntag: git-SHA"]
    I -- PR --> K["Push to ECR\ntag: pr-NUMBER-sha"]
    J --> L["Update image tag\nin aegis-infra\nvia PR / direct commit"]
    L --> M(["Argo CD detects diff\nArgo Rollouts canary begins"])

    style Quality fill:#1e3a5f,stroke:#4a9eff,color:#fff
    style Security fill:#3a1e1e,stroke:#ff4a4a,color:#fff
```

### Workflow File

The pipeline is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Key design decisions:

- **`cargo audit` fails on `RUSTSEC-*` advisories** — no exceptions without explicit ignore annotation in `deny.toml`
- **Trivy blocks on `CRITICAL` and `HIGH` severity** — image cannot be pushed if vulnerabilities are found
- **sccache** caches the Rust build artifacts in GitHub Actions cache, reducing incremental CI build time from ~8 min → ~2 min
- **ECR login** uses OIDC (`id-token: write`) — no long-lived AWS credentials stored in GitHub Secrets

---

## Security Scanning

| Tool           | Stage      | What It Checks                                                                             |
| -------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `cargo clippy` | Lint       | Static analysis: common bugs, non-idiomatic code, potential panics                         |
| `cargo audit`  | SCA        | Known CVEs in `Cargo.lock` dependency tree via [RustSec Advisory DB](https://rustsec.org/) |
| `cargo deny`   | Policy     | License compliance, duplicate dependencies, banned crates                                  |
| Semgrep        | SAST       | Custom rules for Rust: unsafe blocks, SQL injection risks, secret patterns                 |
| Trivy          | Image scan | OS packages and language-level CVEs in final Docker image                                  |

### Cargo Audit Example Output

```
error[RUSTSEC-2023-0052]: Unsound use of `mem::uninitialized`
    ┌─ Cargo.lock:42:1
    │
 42 │ some-crate 0.3.1
    │
    = ID: RUSTSEC-2023-0052
    = Advisory: https://rustsec.org/advisories/RUSTSEC-2023-0052
    = Severity: medium
```

### Trivy Example Output

```
aegis-urban-data-api:git-abc1234 (debian 12.0)
Total: 0 (CRITICAL: 0, HIGH: 0)
```

> [!TIP]
> The distroless base image dramatically reduces the Trivy CVE surface. A full `debian:slim` base typically reports 20–50 `HIGH`+ findings; `distroless/cc` typically reports 0–2.

---

## Architecture Fit in Aegis Platform

This service is deployed in **Sync Wave 3** of the Argo CD App-of-Apps tree, after infrastructure (Wave 1) and CloudNativePG (Wave 2) are ready.

```
Sync Wave 0 → Terraform (network, IAM, ECR, Secrets Manager)
Sync Wave 1 → CRDs: Kyverno, External Secrets Operator, networking
Sync Wave 2 → CloudNativePG cluster (PostgreSQL HA)
Sync Wave 3 → aegis-urban-data-api  ◀── THIS SERVICE
Sync Wave 4 → Frontend + edge services (Ingress, TLS, WAF)
```

### Kubernetes Resource Topology

```
Namespace: urban-data
├── Deployment (managed by Argo Rollouts → CanaryRollout)
│   ├── Replicas: 3 (anti-affinity across zone labels)
│   ├── livenessProbe:  GET /health
│   └── readinessProbe: GET /ready  ← removed from Service on DB failover
├── Service (ClusterIP)
├── HPA (cpu target: 70%) / KEDA (queue depth trigger)
├── ExternalSecret → AWS Secrets Manager → DB credentials
│   └── Projected as: Secret/urban-data-db-credentials
├── ServiceMonitor → Prometheus scrape (/metrics)
└── PodDisruptionBudget (minAvailable: 2)
```

### External Secrets Flow

```
[AWS Secrets Manager]   ←→   [External Secrets Operator]   →   [Kubernetes Secret]
 (Floci locally)               (reads every 1h / on sync)       (mounted as env var)
                                                                          ↓
                                                               [aegis-urban-data-api pod]
                                                               reads DATABASE_URL at startup
```

> [!NOTE]
> The Kyverno policy `require-resource-limits` enforces that this deployment always declares CPU/memory limits. Without limits, HPA cannot function correctly and noisy-neighbour effects could destabilise the k3d cluster.

---

## Related Repository

| Repository                                                             | Purpose                                                                           |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| [`aegis-infra`](https://github.com/your-org/aegis-infra) | Single Source of Truth — Terraform, Helm charts, Kustomize overlays, Argo CD apps |

See the [Aegis Platform README](https://github.com/your-org/aegis-infra/blob/main/README.md) for the full platform architecture, environment strategy, and HA validation methodology.

---

## License

[MIT](LICENSE) — Nguyễn Võ Hoàng, HUTECH University VJIT Program, 2026.
