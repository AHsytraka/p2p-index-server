from fastapi import APIRouter, Depends, UploadFile
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.services.upload_service import UploadService

router = APIRouter()

#dependency injection
def get_upload_file_service(db: Session = Depends(get_db)):
  return UploadService(db)

@router.post("/upload")
async def upload(file: UploadFile, upload_file_service: UploadService = Depends(get_upload_file_service)):
  return await upload_file_service.upload_file(file=file)