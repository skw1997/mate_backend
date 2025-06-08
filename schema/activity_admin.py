from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import Event, EventContent
from pydantic import BaseModel, Field

class PendingActivityItem(BaseModel):
    activity_id: str
    owner_id: str
    submitted_at: str
    status: str

class PendingActivitiesResponse(BaseModel):
    pending_activities: List[PendingActivityItem]

class PendingActivitiesRequest(BaseModel):
    user_id: str
    token: str

class AdminActivityUpdateRequest(BaseModel):
    user_id: str
    token: str
    activity_id: str
    status: str  # "approve" or "reject"
    reviewer_id: str
    comment: str = ""

class AdminActivityUpdateResponse(BaseModel):
    activity_id: str
    new_status: str
    reviewed_at: str