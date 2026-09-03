from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.auth import CurrentUser, require_student
from app.database import get_db
from app.models import Answer, Response, Student, Survey
from app.schemas import ResponseSubmitIn, SurveyDetail, SurveyListItem
from app.sheets import append_row
from app.survey_utils import question_to_out

router = APIRouter(prefix="/api/surveys", tags=["surveys"], dependencies=[Depends(require_student)])


@router.get("", response_model=list[SurveyListItem])
def list_published_surveys(
    db: Session = Depends(get_db), user: CurrentUser = Depends(require_student)
):
    surveys = (
        db.query(Survey)
        .filter(Survey.is_published.is_(True))
        .order_by(Survey.created_at.desc())
        .all()
    )
    result = []
    for s in surveys:
        already = (
            db.query(Response)
            .filter(Response.survey_id == s.id, Response.student_id == user.user_id)
            .first()
            is not None
        )
        result.append(
            SurveyListItem(
                id=s.id,
                title=s.title,
                description=s.description,
                is_published=s.is_published,
                allow_multiple_responses=s.allow_multiple_responses,
                created_at=s.created_at,
                already_submitted=already,
            )
        )
    return result


@router.get("/{survey_id}", response_model=SurveyDetail)
def get_survey(
    survey_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_student)
):
    survey = (
        db.query(Survey)
        .options(selectinload(Survey.questions))
        .filter(Survey.id == survey_id, Survey.is_published.is_(True))
        .first()
    )
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문을 찾을 수 없습니다.")

    already = (
        db.query(Response)
        .filter(Response.survey_id == survey.id, Response.student_id == user.user_id)
        .first()
        is not None
    )
    return SurveyDetail(
        id=survey.id,
        title=survey.title,
        description=survey.description,
        is_published=survey.is_published,
        allow_multiple_responses=survey.allow_multiple_responses,
        sheet_id=survey.sheet_id,
        sheet_tab=survey.sheet_tab,
        created_at=survey.created_at,
        questions=[question_to_out(q) for q in sorted(survey.questions, key=lambda q: q.order)],
        already_submitted=already,
    )


@router.post("/{survey_id}/responses", status_code=status.HTTP_201_CREATED)
def submit_response(
    survey_id: str,
    body: ResponseSubmitIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_student),
):
    survey = (
        db.query(Survey)
        .options(selectinload(Survey.questions))
        .filter(Survey.id == survey_id, Survey.is_published.is_(True))
        .first()
    )
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문을 찾을 수 없습니다.")

    if not survey.allow_multiple_responses:
        existing = (
            db.query(Response)
            .filter(Response.survey_id == survey_id, Response.student_id == user.user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="이미 이 설문에 응답하셨습니다."
            )

    answers_by_q = {a.question_id: a for a in body.answers}
    for q in survey.questions:
        if q.required:
            a = answers_by_q.get(q.id)
            has_value = a and ((a.value and a.value.strip()) or (a.values and len(a.values) > 0))
            if not has_value:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f'"{q.label}" 항목은 필수 입력입니다.',
                )

    question_ids = {q.id for q in survey.questions}
    response = Response(survey_id=survey.id, student_id=user.user_id)
    for a in body.answers:
        if a.question_id not in question_ids:
            continue
        response.answers.append(
            Answer(question_id=a.question_id, value=a.value, value_json=a.values)
        )
    db.add(response)
    db.commit()
    db.refresh(response)

    if survey.sheet_id:
        try:
            questions_sorted = sorted(survey.questions, key=lambda q: q.order)
            row = [
                response.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
                user.name or "",
                _student_number(db, user.user_id),
            ]
            for q in questions_sorted:
                a = answers_by_q.get(q.id)
                if not a:
                    row.append("")
                elif a.values:
                    row.append(", ".join(a.values))
                else:
                    row.append(a.value or "")
            append_row(survey.sheet_id, survey.sheet_tab or "Sheet1", row)
            response.synced_to_sheet = True
            db.commit()
        except Exception:
            pass

    return {"id": response.id}


def _student_number(db: Session, student_id: str | None) -> str:
    if not student_id:
        return ""
    student = db.get(Student, student_id)
    return student.student_id if student else ""
