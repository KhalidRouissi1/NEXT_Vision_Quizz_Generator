from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import random

class QuestionBase(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    difficulty: str
    score: int = Field(default=1, description="Question score/points")

class Question(QuestionBase):
    question_id: str = Field(default_factory=lambda: str(random.randint(1000, 9999)))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class QuizMetadata(BaseModel):
    total_questions: int
    difficulty_distribution: Dict[str, int]
    total_score: int
    estimated_time_minutes: int
    created_at: str

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[Question]
    metadata: QuizMetadata
