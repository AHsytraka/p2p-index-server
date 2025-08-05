from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.base import Base

class DataMapping(Base):
  __tablename__ = "data_mapping"
  uuid=Column(String, primary_key=True, index=True)
  original_name=Column(String, index=True)
  storage_name=Column(String, index=True)
  created_at = Column(DateTime, default=datetime.now)
  