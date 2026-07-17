from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# --------------- SQLAlchemy ORM Models ---------------

class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mood: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(15), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="Light Work")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class MealPlanHistory(Base):
    __tablename__ = "meal_plan_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mood: Mapped[str] = mapped_column(String(20), nullable=False)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


# --------------- Pydantic Schemas ---------------

class MoodManualRequest(BaseModel):
    mood: str


class QuestionnaireRequest(BaseModel):
    answers: list[int]


class MoodResponse(BaseModel):
    id: int
    mood: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "Light Work"
    priority: int = 3
    estimated_minutes: int = 30


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    estimated_minutes: Optional[int] = None
    completed: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    priority: int
    estimated_minutes: int
    completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
