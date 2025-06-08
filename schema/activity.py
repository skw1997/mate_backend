from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import Event, EventContent
from pydantic import BaseModel, Field


#create activity
class ActivityInputData(BaseModel):
    prompt: str
    theme: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[str] = None
    duration: Optional[str] = None
    additional_context: Optional[str] = None

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


#manual create activity
class ManualCreateRequirements(BaseModel):
    group_size: int
    activity_tags: List[str]

class ManualCreateRequest(BaseModel):
    user_id: str
    token: str
    title: str
    description: str
    theme: str
    location: str
    budget: int
    start_time: str  # ISO datetime string
    requirements: ManualCreateRequirements

class ManualCreateResponse(BaseModel):
    activity_id: str
    status: str
    created_at: str

class ActivityCardRequest(BaseModel):
    user_id: str
    token: str
    activity_id: str

class ActivityCardResponse(BaseModel):
    activity_id: str
    title: str
    location: str
    start_time: str

class ActivityDetailRequest(BaseModel):
    user_id: str
    token: str
    activity_id: str

class ActivityDetailRequirements(BaseModel):
    group_size: str
    activity_tags: List[str]
    recommended_equipment: List[str]

class ActivityDetailResponse(BaseModel):
    activity_id: str
    title: str
    description: str
    theme: str
    location: str
    budget: str
    start_time: str
    duration: str
    status: str
    requirements: ActivityDetailRequirements
    participants: List[str]
    created_at: str
    last_updated: str

class ActivityUpdateRequirements(BaseModel):
    group_size: int
    activity_tags: List[str]

class ActivityUpdateRequest(BaseModel):
    user_id: str
    token: str
    activity_id: str
    activity_title: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[int] = None
    start_time: Optional[str] = None
    duration: Optional[float] = None
    requirements: Optional[ActivityUpdateRequirements] = None
    status: Optional[str] = None  # e.g.,"created","pending", "approved", "rejected","cancelled","finished"

class ActivityUpdateResponse(BaseModel):
    activity_id: str
    feedback: str
    updated_at: str



class ActivityFeedbackRequest(BaseModel):
    user_id: str
    token: str
    activity_id: str
    rating: float
    comment: str

class ActivityFeedbackResponse(BaseModel):
    activity_id: str
    rating_id: str
    status: str
    submitted_at: str


class FeedbackItem(BaseModel):
    feedback_id: str
    rating: float
    comment: str
    submitted_at: str

class FeedbackListResponse(BaseModel):
    activity_id: str
    feedbacks: List[FeedbackItem]



class ActivityHistoryItem(BaseModel):
    activity_id: str
    status: str
    timestamp: str

class ActivityHistoryRequest(BaseModel):
    user_id: str
    token: str

class ActivityHistoryResponse(BaseModel):
    user_id: str
    history: List[ActivityHistoryItem]