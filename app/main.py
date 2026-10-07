from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import jobs, certificates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables automatically on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Bulk Certificate Generator API",
    description="""
A robust, asynchronous backend system for generating personalized PDF certificates in bulk.
Features relational tracking, individual failure handling, and resilient progress monitoring.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(jobs.router)
app.include_router(certificates.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Bulk Certificate Generator API",
        "status": "online",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
