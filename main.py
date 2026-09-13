"""
urban-data-api — Application entry point.

Starts the FastAPI application with Uvicorn for local development.
In production (container), CMD in Dockerfile calls uvicorn directly.
"""

import uvicorn

from app.main import create_app

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        "app.main:create_app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        factory=True,
    )
