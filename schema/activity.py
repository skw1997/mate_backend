from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import Event, EventContent
from pydantic import BaseModel, Field

class ActivityInputData(BaseModel):
    prompt: str
    theme: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[str] = None
    duration: Optional[str] = None
    additional_context: Optional[str] = None
    status: Optional[int] = None  # 状态码，0-决定中，1-进行中，2-已完成，3-已取消

class ActivityCreateRequest(BaseModel):
    user_id: str
    token: str
    session_id: str
    input_data: ActivityInputData

class GeneratedActivity(BaseModel):
    title: str
    description: str
    start_time: str
    recommended_equipment: List[str]

class ActivityCreateResponse(BaseModel):
    activity_id: str
    generated_activity: GeneratedActivity
    status: str
    created_at: str