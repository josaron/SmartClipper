import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import jobs

app = FastAPI(
    title="SmartClipper API",
    description="API for generating YouTube shorts from long-form videos",
    version="1.0.0"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp and output directories
os.makedirs("/app/temp", exist_ok=True)
os.makedirs("/app/output", exist_ok=True)

# Mount static files for serving outputs
app.mount("/static", StaticFiles(directory="/app/output"), name="static")

# Include routers
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])


@app.get("/health")
@app.get("/heath")  # Handle typo in Render config
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
