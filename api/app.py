from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import health, log

app = FastAPI(
    title="unilog REST API",
    description="""
A production-quality REST API engine for unilog (Universal Log Parser).
This API handles format auto-detection, parsing log text, generating aggregate metrics,
and asynchronous file uploading with background processing support.
    """,
    version="0.2.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(log.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
