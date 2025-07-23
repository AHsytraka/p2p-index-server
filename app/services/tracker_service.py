from sqlalchemy.orm import Session
from app.db.session import get_db
from fastapi import Depends
from app.models.example import Example

class TrackerService:
  def __init__(self, db: Session = Depends(get_db)):
    self.db = db
  
  def create_example(self, name: str) -> Example:
    example = Example(name=name)
    self.db.add(example)
    self.db.commit()
    self.db.refresh(example)
    return example