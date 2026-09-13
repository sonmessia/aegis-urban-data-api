//! urban-data-api — IoT urban data ingestion service
//! Part of the Aegis Platform Capstone project.
//!
//! This binary is intentionally minimal at bootstrap.
//! See docs/ARCHITECTURE.md for the full design.

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    tracing::info!("urban-data-api starting — Aegis Platform");
}
