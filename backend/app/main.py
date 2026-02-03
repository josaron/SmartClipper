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
cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",")]
# #region agent log
print(f"[DEBUG] CORS_ORIGINS env var: '{cors_origins_raw}'")
print(f"[DEBUG] Parsed CORS origins: {cors_origins}")
# #endregion
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
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy"}


# #region agent log
@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration."""
    return {
        "cors_origins_raw": cors_origins_raw,
        "cors_origins": cors_origins,
        "expected_origin": "https://smart-clipper.vercel.app",
        "is_configured": "https://smart-clipper.vercel.app" in cors_origins
    }
# #endregion


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SmartClipper API",
        "docs": "/docs",
        "health": "/health"
    }
