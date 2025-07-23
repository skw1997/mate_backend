from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import Event, EventContent
from pydantic import BaseModel, Field


class LocationItem(BaseModel):
    name: str
    lat: float
    lng: float
    category: str
    address: str
