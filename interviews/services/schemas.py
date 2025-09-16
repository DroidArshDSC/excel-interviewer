from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class GeneratedQuestion(BaseModel):
    type: str                 # "theory" | "practical"
    title: str
    spec: Dict[str, Any]
    rubric: Dict[str, Any]
    ideal_answer: Optional[str] = None
    version: Optional[int] = 1

class RunnerResult(BaseModel):
    passed: bool
    checks: List[Dict[str, Any]]
    score_runner: float

class JudgeResult(BaseModel):
    score: float
    verdict: str
    mistakes: List[str]
    improvements: List[str]
    citations: List[str]
