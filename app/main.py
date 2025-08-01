from fastapi import FastAPI
from app.api import tracker
from app.api import upload
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

#Init app
app = FastAPI(title= settings.PROJECT_NAME)

#Create tables
Base.metadata.create_all(bind=engine)

#Load routers
app.include_router(tracker.router, prefix="/api/tracker", tags=["Users"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])