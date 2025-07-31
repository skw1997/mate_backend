from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import Event, EventContent
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import SQLModel  # Import SQLModel


class LocationItem(BaseModel):
    name: str
    lat: float
    lng: float
    category: str
    address: str

class UserLocationRequest(BaseModel):
    user_id: str
    location: dict  # {"lat": float, "lng": float}
    timestamp: str

class UserLocationResponse(BaseModel):
    user_id: str
    status: str
    updated_at: str
