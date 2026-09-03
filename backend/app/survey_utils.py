from fastapi import HTTPException, status

from app.models import Question, QuestionType
from app.schemas import LinearScaleOptions, QuestionIn, QuestionOut

CHOICE_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.DROPDOWN}


def validate_question_input(q: QuestionIn) -> None:
    if q.type in CHOICE_TYPES:
        if not q.choices or len(q.choices) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'"{q.label}" 질문에는 선택지를 2개 이상 입력해주세요.',
            )
    if q.type == QuestionType.LINEAR_SCALE:
        if not q.linear_scale:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'"{q.label}" 질문의 배율 범위를 입력해주세요.',
            )
        if q.linear_scale.max <= q.linear_scale.min:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f'"{q.label}" 질문의 최대값은 최소값보다 커야 합니다.',
            )


def serialize_options(q: QuestionIn) -> dict | None:
    if q.type in CHOICE_TYPES:
        return {"kind": "choices", "choices": q.choices or []}
    if q.type == QuestionType.LINEAR_SCALE and q.linear_scale:
        return {
            "kind": "linearScale",
            "min": q.linear_scale.min,
            "max": q.linear_scale.max,
            "minLabel": q.linear_scale.min_label,
            "maxLabel": q.linear_scale.max_label,
        }
    return None


def question_to_out(q: Question) -> QuestionOut:
    choices = None
    linear_scale = None
    if q.options:
        if q.options.get("kind") == "choices":
            choices = q.options.get("choices", [])
        elif q.options.get("kind") == "linearScale":
            linear_scale = LinearScaleOptions(
                min=q.options.get("min", 1),
                max=q.options.get("max", 5),
                min_label=q.options.get("minLabel"),
                max_label=q.options.get("maxLabel"),
            )
    return QuestionOut(
        id=q.id,
        type=q.type,
        label=q.label,
        description=q.description,
        required=q.required,
        choices=choices,
        linear_scale=linear_scale,
        order=q.order,
    )
