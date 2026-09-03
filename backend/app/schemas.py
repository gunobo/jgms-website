from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import QuestionType

# --- Auth ---


class GoogleLoginIn(BaseModel):
    credential: str


class MeOut(BaseModel):
    email: str
    role: Literal["admin", "student", "unregistered"]
    name: str | None = None
    user_id: str | None = None


# --- Students ---


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    student_id: str = Field(min_length=1, max_length=30)
    email: EmailStr
    grade: str | None = Field(default=None, max_length=20)
    class_name: str | None = Field(default=None, max_length=20)


class StudentOut(BaseModel):
    id: str
    name: str
    student_id: str
    email: str
    grade: str | None
    class_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentBulkCreate(BaseModel):
    text: str


class StudentBulkResult(BaseModel):
    created: int
    skipped: list[str]


# --- Admins ---


class AdminCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=100)


class AdminOut(BaseModel):
    id: str
    email: str
    name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Surveys / Questions ---


class LinearScaleOptions(BaseModel):
    min: int = Field(ge=0, le=10)
    max: int = Field(ge=1, le=10)
    min_label: str | None = Field(default=None, max_length=50)
    max_label: str | None = Field(default=None, max_length=50)


class QuestionIn(BaseModel):
    id: str | None = None
    type: QuestionType
    label: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=1000)
    required: bool = False
    choices: list[str] | None = None
    linear_scale: LinearScaleOptions | None = None
    order: int = 0

    @field_validator("choices")
    @classmethod
    def strip_choices(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return [c.strip() for c in v if c.strip()]


class QuestionOut(BaseModel):
    id: str
    type: QuestionType
    label: str
    description: str | None
    required: bool
    choices: list[str] | None = None
    linear_scale: LinearScaleOptions | None = None
    order: int

    model_config = {"from_attributes": True}


class SurveyCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    allow_multiple_responses: bool = False
    questions: list[QuestionIn] = Field(min_length=1)


class SurveyListItem(BaseModel):
    id: str
    title: str
    description: str | None
    is_published: bool
    allow_multiple_responses: bool
    created_at: datetime
    response_count: int = 0
    already_submitted: bool = False

    model_config = {"from_attributes": True}


class SurveyDetail(BaseModel):
    id: str
    title: str
    description: str | None
    is_published: bool
    allow_multiple_responses: bool
    sheet_id: str | None
    sheet_tab: str | None
    created_at: datetime
    questions: list[QuestionOut]
    already_submitted: bool = False

    model_config = {"from_attributes": True}


# --- Responses ---


class AnswerIn(BaseModel):
    question_id: str
    value: str | None = None
    values: list[str] | None = None


class ResponseSubmitIn(BaseModel):
    answers: list[AnswerIn]


class AnswerOut(BaseModel):
    question_id: str
    value: str | None
    values: list[str] | None = None


class ResponseOut(BaseModel):
    id: str
    submitted_at: datetime
    student_name: str
    student_number: str
    synced_to_sheet: bool
    answers: list[AnswerOut]


class SheetLinkIn(BaseModel):
    sheet_url_or_id: str = Field(min_length=1)


# --- Assignments / Rubric grading ---


class RubricItemIn(BaseModel):
    id: str | None = None
    label: str = Field(min_length=1, max_length=500)
    points: int = Field(ge=0, le=1000)
    order: int = 0


class RubricCriterionIn(BaseModel):
    id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    order: int = 0
    items: list[RubricItemIn] = Field(min_length=1)


class AssignmentCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    criteria: list[RubricCriterionIn] = Field(min_length=1)


class RubricItemOut(RubricItemIn):
    id: str


class RubricCriterionOut(BaseModel):
    id: str
    title: str
    description: str | None
    order: int
    items: list[RubricItemOut]


class AssignmentListItem(BaseModel):
    id: str
    title: str
    description: str | None
    is_published: bool
    created_at: datetime
    max_score: int
    submission_count: int = 0
    already_submitted: bool = False
    my_score: int | None = None


class AssignmentDetail(BaseModel):
    id: str
    title: str
    description: str | None
    is_published: bool
    sheet_id: str | None
    rubric_sheet_tab: str | None
    scores_sheet_tab: str | None
    created_at: datetime
    criteria: list[RubricCriterionOut]
    max_score: int


class SubmissionOut(BaseModel):
    id: str
    link_url: str | None
    text_content: str | None
    file_name: str | None
    submitted_at: datetime
    updated_at: datetime


class GradeOut(BaseModel):
    id: str
    checked_item_ids: list[str]
    total_score: int
    max_score: int
    comment: str | None
    graded_at: datetime
    graded_by_name: str | None


class SubmissionWithGradeOut(BaseModel):
    submission: SubmissionOut
    student_name: str
    student_number: str
    grade: GradeOut | None = None


class MySubmissionOut(BaseModel):
    submission: SubmissionOut | None = None
    grade: GradeOut | None = None


class GradeIn(BaseModel):
    checked_item_ids: list[str] = Field(default_factory=list)
    comment: str | None = Field(default=None, max_length=2000)
