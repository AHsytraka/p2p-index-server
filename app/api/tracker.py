from fastapi import APIRouter


router = APIRouter()

@router.get("/")
def something():
  return {"something":"something"};