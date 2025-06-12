from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from database.lifetime import get_session
from schema.database import ActivityMatch, MatchRecord, MatchFeedbackRecord
from pydantic import BaseModel, Field

class MatchCriteria(BaseModel):
    preferred_tags: list[str] = Field(default_factory=list)
    location: str = ""
    age_range: list[int] = Field(default_factory=list)
    max_distance_km: int = 0

class MatchCandidatesRequest(BaseModel):
    user_id: str
    activity_id: str
    token: str
    criteria: MatchCriteria

class MatchedCandidate(BaseModel):
    user_id: str
    similarity_score: float

class MatchCandidatesResponse(BaseModel):
    activity_id: str
    match_id: str
    matched_candidates: list[MatchedCandidate]
    user_pending: list[str]
    user_accepted: list[str]
    user_rejected: list[str]
    matched_at: str
    status: str

class MatchRecordQueryRequest(BaseModel):
    user_id: str
    activity_id: str
    token: str

class MatchRecordQueryResponse(BaseModel):
    activity_id: str
    match_record_id: str
    matched_candidates: list[MatchedCandidate]
    user_pending: list[str]
    user_accepted: list[str]
    user_rejected: list[str]
    matched_at: str
    status: str

class MatchFeedbackRequest(BaseModel):
    user_id: str
    activity_id: str
    match_id: str
    token: str
    rating: str

class MatchFeedbackResponse(BaseModel):
    activity_id: str
    message: str


class MatchStatusResponse(BaseModel):
    activity_id: str
    user_id: str
    matching_status: str
    current_candidates_count: int

class MatchUpdateRequest(BaseModel):
    user_id: str
    activity_id: str
    token: str
    action: str  # "cancelled" 或 "paused"

class MatchUpdateResponse(BaseModel):
    activity_id: str
    status: str
    timestamp: str

class MatchNotificationActionRequest(BaseModel):
    user_id: str
    token: str
    match_id: str
    response: str  # "accept" 或 "reject"

class MatchNotificationActionResponse(BaseModel):
    match_id: str
    message: str