from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class ExerciseCreate(BaseModel):
    name: str
    description: str
    category: str

class WorkoutCreate(BaseModel):
    exercise_id: int
    sets: int
    repetitions: int
    weights: Optional[float]    

class WorkoutDelete(BaseModel):
    exercise_id: int