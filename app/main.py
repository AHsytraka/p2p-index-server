from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tracker
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import models to ensure they are registered with SQLAlchemy
from app.models import torrent, peer, user

# Init app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="P2P BitTorrent-like File Sharing Tracker",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Load routers
app.include_router(tracker.router, prefix="/api/tracker", tags=["Tracker"])

@app.get("/")
def read_root():
    return {
        "message": "P2P BitTorrent-like Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
