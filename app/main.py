from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import atexit
from app.api import tracker
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services.auto_seeder_service import auto_seeder_manager

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
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Start auto seeder manager
auto_seeder_manager.start_manager()

# Register cleanup on app shutdown
atexit.register(auto_seeder_manager.stop_manager)

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
