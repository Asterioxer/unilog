import time
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi.errors import RateLimitExceeded

from api.routers import health, log
from api.dependencies.rate_limiter import limiter

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("unilog-api")

app = FastAPI(
    title="unilog REST API",
    description="""
A production-ready platform API for unilog (Universal Log Parser).
This API handles format auto-detection, parsing log text, generating aggregate statistics,
and asynchronous file uploads with background task execution.
    """,
    version="0.2.0-beta",
    contact={
        "name": "unilog Developer Team",
        "url": "https://github.com/Asterioxer/unilog",
        "email": "sohamaxpauli@gmail.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/Asterioxer/unilog/blob/main/LICENSE"
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup slowapi rate limiter configuration
app.state.limiter = limiter

# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Limit is 100 requests per minute per IP.",
                "details": {}
            }
        }
    )

# Custom HTTP exception handler implementing unified error format
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    code = "API_ERROR"
    if exc.status_code == 400:
        code = "INVALID_LOG"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 413:
        code = "FILE_TOO_LARGE"
    elif exc.status_code == 422:
        code = "UNPROCESSABLE_ENTITY"
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": str(exc.detail),
                "details": {}
            }
        }
    )

# Global catch-all handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected server error occurred: {exc}",
                "details": {}
            }
        }
    )

# Middleware for X-Request-ID, X-Response-Time, and structured logging
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Log failure before crash
        logger.error(
            "request_method=%s request_path=%s status_code=500 error=%s request_id=%s",
            request.method, request.url.path, str(exc), request_id
        )
        raise exc
        
    process_time = (time.time() - start_time) * 1000
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{process_time:.2f}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    
    # Structured key-value logging (logfmt)
    logger.info(
        "request_method=%s request_path=%s status_code=%d duration_ms=%.2f request_id=%s",
        request.method, request.url.path, response.status_code, process_time, request_id
    )
    return response

# Enable gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)  # root health checks (/health, /live, /ready)
app.include_router(log.router, prefix="/api/v1")  # versioned endpoints

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
