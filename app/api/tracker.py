from sqlalchemy.orm import Session
from app.db.session import get_db
from fastapi import Depends
from fastapi import APIRouter
from app.services.tracker_service import TrackerService

router = APIRouter()

#dependency injection
def get_tracker_service(db: Session = Depends(get_db)):
  return TrackerService(db)

@router.post("/create-example")
def create(name: str, tracker_service: TrackerService = Depends(get_tracker_service)):
  return tracker_service.create_example(name=name)
