from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, create_engine
from datetime import datetime
from sqlalchemy import Column, JSON, DateTime, Float, Integer, String, select
from typing import List, Optional, Dict

class ActivityMatch(SQLModel, table=True):
    __tablename__ = "activity_match"

    match_id: str = Field(primary_key=True)
    activity_id: str =  Field(sa_column=Column(JSON))
    status: str
    matched_candidates: List[str] = Field(sa_column=Column(JSON))
    pending: List[str] = Field(sa_column=Column(JSON))
    accepted: List[str] = Field(sa_column=Column(JSON))
    rejected: List[str] = Field(sa_column=Column(JSON))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))

class MatchRecord(SQLModel, table=True):
    __tablename__ = "match_record"

    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: str = Field(foreign_key="activity_match.match_id")
    action: str
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))

class MatchFeedbackRecord(SQLModel, table=True):
    __tablename__ = "match_fb_record"

    id: Optional[int] = Field(default=None, primary_key=True)
    rater_id: str
    match_id: str = Field(foreign_key="activity_match.match_id")
    rating: float
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))