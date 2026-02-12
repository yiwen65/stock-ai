# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import stock

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

# Include routers
app.include_router(stock.router, prefix=f"{settings.API_V1_STR}/stock", tags=["stock"])

@app.get("/")
async def root():
    return {"message": "Stock AI API", "version": settings.VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}
