# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import stock, strategy, analysis, auth
from app.core.rate_limit import rate_limiter

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    key = f"rate_limit:global:{client_ip}"

    if not await rate_limiter.check_rate_limit(key):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )

    response = await call_next(request)
    return response

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(stock.router, prefix=f"{settings.API_V1_STR}/stock", tags=["stock"])
app.include_router(strategy.router, prefix=f"{settings.API_V1_STR}/strategies", tags=["strategies"])
app.include_router(analysis.router, prefix=f"{settings.API_V1_STR}/stocks", tags=["analysis"])

@app.get("/")
async def root():
    return {"message": "Stock AI API", "version": settings.VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}
