import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import jobs
from app.config import TEMP_DIR, OUTPUT_DIR

app = FastAPI(
    title="SmartClipper API",
    description="API for generating YouTube shorts from long-form videos",
    version="1.0.0"
)

# CORS configuration
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# Strip whitespace and trailing slashes from origins (common config mistakes)
cors_origins = [origin.strip().rstrip("/") for origin in cors_origins_raw.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving outputs
app.mount("/static", StaticFiles(directory=OUTPUT_DIR), name="static")

# Include routers
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SmartClipper API",
        "docs": "/docs",
        "health": "/health"
    }
