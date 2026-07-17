from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MoodEntry, MoodManualRequest, MoodResponse, QuestionnaireRequest

router = APIRouter(prefix="/api/mood", tags=["mood"])

VALID_MOODS = ["Happy", "Stressed", "Tired", "Focused", "Anxious", "Energetic", "Sad"]

QUESTIONS = [
    {
        "text": "How well did you sleep last night?",
        "options": [
            {"label": "Terribly", "energy": 0, "stress": 2},
            {"label": "Poorly", "energy": 1, "stress": 1},
            {"label": "Okay", "energy": 2, "stress": 1},
            {"label": "Great", "energy": 3, "stress": 0},
        ],
    },
    {
        "text": "How does your body feel right now?",
        "options": [
            {"label": "Tense and restless", "energy": 1, "stress": 3},
            {"label": "Heavy and sluggish", "energy": 0, "stress": 1},
            {"label": "Neutral", "energy": 2, "stress": 1},
            {"label": "Light and comfortable", "energy": 3, "stress": 0},
        ],
    },
    {
        "text": "How clear is your thinking?",
        "options": [
            {"label": "Foggy and scattered", "energy": 0, "stress": 2},
            {"label": "A bit distracted", "energy": 1, "stress": 1},
            {"label": "Reasonably clear", "energy": 2, "stress": 0},
            {"label": "Sharp and focused", "energy": 3, "stress": 0},
        ],
    },
    {
        "text": "How do you feel about being around people today?",
        "options": [
            {"label": "I want to be alone", "energy": 0, "stress": 2},
            {"label": "Small groups are fine", "energy": 1, "stress": 1},
            {"label": "I'm open to socializing", "energy": 2, "stress": 0},
            {"label": "I'm craving connection", "energy": 3, "stress": 0},
        ],
    },
    {
        "text": "How motivated do you feel to work?",
        "options": [
            {"label": "Not at all", "energy": 0, "stress": 1},
            {"label": "Only for easy stuff", "energy": 1, "stress": 1},
            {"label": "Ready for moderate tasks", "energy": 2, "stress": 0},
            {"label": "Bring on the challenges", "energy": 3, "stress": 0},
        ],
    },
]


def _infer_mood(answers: list[int]) -> str:
    energy_total = 0
    stress_total = 0
    for i, answer_idx in enumerate(answers):
        idx = max(0, min(answer_idx, 3))
        energy_total += QUESTIONS[i]["options"][idx]["energy"]
        stress_total += QUESTIONS[i]["options"][idx]["stress"]

    if energy_total >= 10 and stress_total <= 4:
        return "Energetic"
    if energy_total >= 10 and stress_total > 4:
        return "Anxious"
    if energy_total >= 6 and stress_total <= 3:
        return "Happy"
    if energy_total >= 6 and stress_total <= 5:
        return "Focused"
    if energy_total >= 6:
        return "Stressed"
    if stress_total <= 4:
        return "Sad"
    return "Tired"


@router.get("/questions")
def get_questions():
    return QUESTIONS


@router.post("/manual", response_model=MoodResponse)
def set_mood_manual(req: MoodManualRequest, db: Session = Depends(get_db)):
    mood = req.mood.capitalize()
    if mood not in VALID_MOODS:
        mood = "Happy"
    entry = MoodEntry(mood=mood, source="manual")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/questionnaire", response_model=MoodResponse)
def set_mood_questionnaire(req: QuestionnaireRequest, db: Session = Depends(get_db)):
    answers = req.answers[:5]
    while len(answers) < 5:
        answers.append(2)
    mood = _infer_mood(answers)
    entry = MoodEntry(mood=mood, source="questionnaire")
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/current", response_model=MoodResponse | None)
def get_current_mood(db: Session = Depends(get_db)):
    entry = db.query(MoodEntry).order_by(desc(MoodEntry.created_at)).first()
    return entry


@router.get("/history", response_model=list[MoodResponse])
def get_mood_history(limit: int = 10, db: Session = Depends(get_db)):
    return (
        db.query(MoodEntry)
        .order_by(desc(MoodEntry.created_at))
        .limit(limit)
        .all()
    )
