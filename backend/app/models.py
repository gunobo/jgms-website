import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class QuestionType(str, enum.Enum):
    SHORT_TEXT = "SHORT_TEXT"
    PARAGRAPH = "PARAGRAPH"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    DROPDOWN = "DROPDOWN"
    LINEAR_SCALE = "LINEAR_SCALE"


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    surveys: Mapped[list["Survey"]] = relationship(back_populates="created_by")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    student_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    class_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    responses: Mapped[list["Response"]] = relationship(back_populates="student")


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_multiple_responses: Mapped[bool] = mapped_column(Boolean, default=False)
    sheet_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sheet_tab: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by_id: Mapped[str] = mapped_column(ForeignKey("admins.id"))
    created_by: Mapped["Admin"] = relationship(back_populates="surveys")

    questions: Mapped[list["Question"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan", order_by="Question.order"
    )
    responses: Mapped[list["Response"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType, native_enum=False, length=20))
    label: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    survey_id: Mapped[str] = mapped_column(ForeignKey("surveys.id"))
    survey: Mapped["Survey"] = relationship(back_populates="questions")

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class Response(Base):
    __tablename__ = "responses"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    synced_to_sheet: Mapped[bool] = mapped_column(Boolean, default=False)

    survey_id: Mapped[str] = mapped_column(ForeignKey("surveys.id"))
    survey: Mapped["Survey"] = relationship(back_populates="responses")

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"))
    student: Mapped["Student"] = relationship(back_populates="responses")

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="response", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    response_id: Mapped[str] = mapped_column(ForeignKey("responses.id"))
    response: Mapped["Response"] = relationship(back_populates="answers")

    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["Question"] = relationship(back_populates="answers")


# --- Assignments / Rubric grading ---


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    sheet_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rubric_sheet_tab: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scores_sheet_tab: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by_id: Mapped[str] = mapped_column(ForeignKey("admins.id"))
    created_by: Mapped["Admin"] = relationship()

    criteria: Mapped[list["RubricCriterion"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan", order_by="RubricCriterion.order"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    assignment: Mapped["Assignment"] = relationship(back_populates="criteria")

    items: Mapped[list["RubricItem"]] = relationship(
        back_populates="criterion", cascade="all, delete-orphan", order_by="RubricItem.order"
    )


class RubricItem(Base):
    __tablename__ = "rubric_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    label: Mapped[str] = mapped_column(String(500))
    points: Mapped[int] = mapped_column(Integer, default=0)
    order: Mapped[int] = mapped_column(Integer, default=0)

    criterion_id: Mapped[str] = mapped_column(ForeignKey("rubric_criteria.id"))
    criterion: Mapped["RubricCriterion"] = relationship(back_populates="items")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    link_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"))
    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"))
    student: Mapped["Student"] = relationship()

    grade: Mapped["Grade | None"] = relationship(
        back_populates="submission", cascade="all, delete-orphan", uselist=False
    )


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    checked_item_ids: Mapped[list] = mapped_column(JSON, default=list)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    synced_to_sheet: Mapped[bool] = mapped_column(Boolean, default=False)

    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), unique=True)
    submission: Mapped["Submission"] = relationship(back_populates="grade")

    graded_by_id: Mapped[str] = mapped_column(ForeignKey("admins.id"))
    graded_by: Mapped["Admin"] = relationship()
