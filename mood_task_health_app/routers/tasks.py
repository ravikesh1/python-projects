import json
import os
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MoodEntry, Task, TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

MOOD_PRIORITY = {
    "Tired": {"prefer": ["Self-Care", "Light Work", "Administrative", "Creative", "Deep Work"], "energy_cap": 30},
    "Focused": {"prefer": ["Deep Work", "Creative", "Administrative", "Light Work", "Self-Care"], "energy_cap": 120},
    "Stressed": {"prefer": ["Self-Care", "Light Work", "Administrative", "Creative", "Deep Work"], "energy_cap": 25},
    "Anxious": {"prefer": ["Self-Care", "Light Work", "Administrative", "Creative", "Deep Work"], "energy_cap": 20},
    "Happy": {"prefer": ["Creative", "Deep Work", "Light Work", "Administrative", "Self-Care"], "energy_cap": 90},
    "Energetic": {"prefer": ["Deep Work", "Creative", "Administrative", "Light Work", "Self-Care"], "energy_cap": 120},
    "Sad": {"prefer": ["Self-Care", "Light Work", "Creative", "Administrative", "Deep Work"], "energy_cap": 30},
}

_suggestions_cache: dict | None = None


def _load_suggestions() -> dict:
    global _suggestions_cache
    if _suggestions_cache is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "mood_tasks.json")
        with open(path) as f:
            _suggestions_cache = json.load(f)
    return _suggestions_cache


def _get_current_mood(db: Session) -> str:
    entry = db.query(MoodEntry).order_by(desc(MoodEntry.created_at)).first()
    return entry.mood if entry else "Happy"


def _sort_tasks_by_mood(tasks: list[Task], mood: str) -> list[Task]:
    config = MOOD_PRIORITY.get(mood, MOOD_PRIORITY["Happy"])
    prefer = config["prefer"]
    energy_cap = config["energy_cap"]

    def sort_key(task: Task):
        try:
            cat_rank = prefer.index(task.category)
        except ValueError:
            cat_rank = len(prefer)
        over_cap = 1 if task.estimated_minutes > energy_cap else 0
        return (task.completed, over_cap, cat_rank, -task.priority)

    return sorted(tasks, key=sort_key)


@router.get("", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    mood = _get_current_mood(db)
    tasks = db.query(Task).all()
    return _sort_tasks_by_mood(tasks, mood)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(req: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**req.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, req: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}


@router.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db)):
    mood = _get_current_mood(db)
    all_suggestions = _load_suggestions()
    suggestions = all_suggestions.get(mood, all_suggestions.get("Happy", []))
    random.shuffle(suggestions)
    return {"mood": mood, "suggestions": suggestions}
