from enum import Enum
from pydantic import BaseModel, Field


class CandidateLevel(str, Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


class ReviewRequest(BaseModel):
    assignment_description: str
    github_repo_url: str
    candidate_level: CandidateLevel


class ReviewResponse(BaseModel):
    comments: str
    rating: int = Field(ge=1, le=5)
    conclusion: str
