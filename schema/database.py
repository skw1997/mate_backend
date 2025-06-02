from sqlalchemy.exc import OperationalError
from sqlmodel import Field, Session, SQLModel, create_engine
from datetime import datetime
from sqlalchemy import Column, JSON, DateTime, Float, Integer, String, select
from typing import List, Optional, Dict

class Event(SQLModel, table=True):
    __tablename__ = "event"
    
    activity_id: str = Field(primary_key=True)
    owner_id: str
    participants_id: List[str] = Field(sa_column=Column(JSON))
    status: str
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    rating: Optional[float] = Field(sa_column=Column(Float))
    rating_id: List[str] = Field(sa_column=Column(JSON))

class EventContent(SQLModel, table=True):
    __tablename__ = "event_content"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: str = Field(foreign_key="event.activity_id")
    title: str
    description: str
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    duration: Optional[float] = Field(sa_column=Column(Float))
    theme: str
    location: str
    budget: int
    group_size: int
    recommended_equipment: List[str] = Field(sa_column=Column(JSON))
    activity_tags: List[str] = Field(sa_column=Column(JSON))

class EventRating(SQLModel, table=True):
    __tablename__ = "event_rating"
    
    rating_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    activity_id: str = Field(foreign_key="event.activity_id")
    rater_id: str
    comment: str

class PartnerRating(SQLModel, table=True):
    __tablename__ = "partner_rating"
    
    rating_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    user_id: str
    tags: List[str] = Field(sa_column=Column(JSON))
    comment: str

class EventReview(SQLModel, table=True):
    __tablename__ = "event_review"
    
    review_id: str = Field(primary_key=True)
    status: str
    submitted_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    activity_id: str = Field(foreign_key="event.activity_id")
    reviewer_id: str
    comment: str

