from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router as api_router
from app.db.database import init_db

# Initialize SQLite Local Demo Operational Persistence
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API Orchestration Layer for FinRecon Financial Reconciliation System"
)

# Custom Exception Handler for NotImplementedError (e.g. Unconfigured REAL_MAINFRAME mode)
@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError):
    return JSONResponse(
        status_code=501,
        content={
            "detail": str(exc),
            "mode": settings.FINRECON_MODE,
            "hint": "Set FINRECON_MODE=LOCAL_DEMO to run the integrated local processing engine."
        }
    )

# Enable Configured CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modern Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' http: https: data: blob:;"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "mode": settings.FINRECON_MODE,
        "docs_url": "/docs",
        "health_url": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)

