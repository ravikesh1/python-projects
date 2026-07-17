import json
import os
import random

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MealPlanHistory, MoodEntry

router = APIRouter(prefix="/api/meals", tags=["meals"])

_meals_cache: dict | None = None


def _load_meal_plans() -> dict:
    global _meals_cache
    if _meals_cache is None:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "meal_plans.json")
        with open(path) as f:
            _meals_cache = json.load(f)
    return _meals_cache


def _get_current_mood(db: Session) -> str:
    entry = db.query(MoodEntry).order_by(desc(MoodEntry.created_at)).first()
    return entry.mood if entry else "Happy"


def _generate_plan(mood: str) -> dict:
    all_plans = _load_meal_plans()
    mood_data = all_plans.get(mood, all_plans.get("Happy", {}))

    plan = {}
    for meal_type in ["breakfast", "lunch", "dinner"]:
        options = mood_data.get(meal_type, [])
        if options:
            plan[meal_type] = random.choice(options)
        else:
            plan[meal_type] = {"name": "Balanced meal", "tip": "Eat a variety of whole foods"}

    snack_options = mood_data.get("snacks", [])
    if len(snack_options) >= 2:
        plan["snacks"] = random.sample(snack_options, 2)
    else:
        plan["snacks"] = snack_options

    return plan


@router.get("/plan")
def get_meal_plan(db: Session = Depends(get_db)):
    mood = _get_current_mood(db)
    plan = _generate_plan(mood)

    history_entry = MealPlanHistory(mood=mood, plan_json=json.dumps(plan))
    db.add(history_entry)
    db.commit()

    return {"mood": mood, "plan": plan}


@router.get("/history")
def get_meal_history(limit: int = 10, db: Session = Depends(get_db)):
    entries = (
        db.query(MealPlanHistory)
        .order_by(desc(MealPlanHistory.created_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "mood": e.mood,
            "plan": json.loads(e.plan_json),
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
