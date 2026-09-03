from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.auth import CurrentUser, require_admin
from app.database import get_db
from app.models import Question, Response, Survey
from app.schemas import (
    AnswerOut,
    QuestionOut,
    ResponseOut,
    SheetLinkIn,
    SurveyCreateIn,
    SurveyDetail,
    SurveyListItem,
)
from app.sheets import append_row, extract_spreadsheet_id, is_sheets_configured, make_tab_name, write_header
from app.survey_utils import question_to_out, serialize_options, validate_question_input

router = APIRouter(
    prefix="/api/admin/surveys", tags=["admin-surveys"], dependencies=[Depends(require_admin)]
)


def _get_survey_or_404(db: Session, survey_id: str) -> Survey:
    survey = (
        db.query(Survey)
        .options(selectinload(Survey.questions))
        .filter(Survey.id == survey_id)
        .first()
    )
    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="설문을 찾을 수 없습니다.")
    return survey


def _to_detail(survey: Survey) -> SurveyDetail:
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
    )


@router.get("", response_model=list[SurveyListItem])
def list_surveys(db: Session = Depends(get_db)):
    surveys = db.query(Survey).order_by(Survey.created_at.desc()).all()
    result = []
    for s in surveys:
        count = db.query(Response).filter(Response.survey_id == s.id).count()
        result.append(
            SurveyListItem(
                id=s.id,
                title=s.title,
                description=s.description,
                is_published=s.is_published,
                allow_multiple_responses=s.allow_multiple_responses,
                created_at=s.created_at,
                response_count=count,
            )
        )
    return result


@router.post("", response_model=SurveyDetail, status_code=status.HTTP_201_CREATED)
def create_survey(
    body: SurveyCreateIn, db: Session = Depends(get_db), user: CurrentUser = Depends(require_admin)
):
    for q in body.questions:
        validate_question_input(q)

    survey = Survey(
        title=body.title,
        description=body.description,
        allow_multiple_responses=body.allow_multiple_responses,
        created_by_id=user.user_id,
    )
    for i, q in enumerate(body.questions):
        survey.questions.append(
            Question(
                type=q.type,
                label=q.label,
                description=q.description,
                required=q.required,
                options=serialize_options(q),
                order=i,
            )
        )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return _to_detail(survey)


@router.get("/{survey_id}", response_model=SurveyDetail)
def get_survey(survey_id: str, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    return _to_detail(survey)


@router.put("/{survey_id}", response_model=SurveyDetail)
def update_survey(survey_id: str, body: SurveyCreateIn, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)

    for q in body.questions:
        validate_question_input(q)

    survey.title = body.title
    survey.description = body.description
    survey.allow_multiple_responses = body.allow_multiple_responses

    existing_by_id = {q.id: q for q in survey.questions}
    incoming_ids = {q.id for q in body.questions if q.id}

    for existing_id, existing_q in list(existing_by_id.items()):
        if existing_id not in incoming_ids:
            survey.questions.remove(existing_q)

    for i, q in enumerate(body.questions):
        options = serialize_options(q)
        if q.id and q.id in existing_by_id:
            target = existing_by_id[q.id]
            target.type = q.type
            target.label = q.label
            target.description = q.description
            target.required = q.required
            target.options = options
            target.order = i
        else:
            survey.questions.append(
                Question(
                    type=q.type,
                    label=q.label,
                    description=q.description,
                    required=q.required,
                    options=options,
                    order=i,
                )
            )

    db.commit()
    db.refresh(survey)
    return _to_detail(survey)


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_survey(survey_id: str, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    db.delete(survey)
    db.commit()


@router.post("/{survey_id}/publish", response_model=SurveyDetail)
def set_published(survey_id: str, published: bool, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    survey.is_published = published
    db.commit()
    db.refresh(survey)
    return _to_detail(survey)


@router.post("/{survey_id}/sheet", response_model=SurveyDetail)
def link_sheet(survey_id: str, body: SheetLinkIn, db: Session = Depends(get_db)):
    if not is_sheets_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서버에 Google Sheets 서비스 계정이 설정되어 있지 않습니다.",
        )
    survey = _get_survey_or_404(db, survey_id)
    sheet_id = extract_spreadsheet_id(body.sheet_url_or_id)
    sheet_tab = survey.sheet_tab or make_tab_name(survey.title, survey.id)

    try:
        write_header(
            sheet_id, sheet_tab, [q.label for q in sorted(survey.questions, key=lambda q: q.order)]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="스프레드시트에 연결할 수 없습니다. 시트를 서비스 계정과 공유했는지 확인해주세요.",
        ) from exc

    survey.sheet_id = sheet_id
    survey.sheet_tab = sheet_tab
    db.commit()
    db.refresh(survey)
    return _to_detail(survey)


@router.delete("/{survey_id}/sheet", response_model=SurveyDetail)
def unlink_sheet(survey_id: str, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    survey.sheet_id = None
    db.commit()
    db.refresh(survey)
    return _to_detail(survey)


@router.get("/{survey_id}/responses", response_model=list[ResponseOut])
def list_responses(survey_id: str, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    responses = (
        db.query(Response)
        .options(selectinload(Response.answers), selectinload(Response.student))
        .filter(Response.survey_id == survey_id)
        .order_by(Response.submitted_at.desc())
        .all()
    )
    out = []
    for r in responses:
        answers = [
            AnswerOut(question_id=a.question_id, value=a.value, values=a.value_json)
            for a in r.answers
        ]
        out.append(
            ResponseOut(
                id=r.id,
                submitted_at=r.submitted_at,
                student_name=r.student.name,
                student_number=r.student.student_id,
                synced_to_sheet=r.synced_to_sheet,
                answers=answers,
            )
        )
    return out


@router.post("/{survey_id}/sheet/resync", response_model=dict)
def resync_sheet(survey_id: str, db: Session = Depends(get_db)):
    survey = _get_survey_or_404(db, survey_id)
    if not survey.sheet_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="연결된 스프레드시트가 없습니다.")

    questions = sorted(survey.questions, key=lambda q: q.order)
    write_header(survey.sheet_id, survey.sheet_tab or "Sheet1", [q.label for q in questions])

    responses = (
        db.query(Response)
        .options(selectinload(Response.answers), selectinload(Response.student))
        .filter(Response.survey_id == survey_id)
        .order_by(Response.submitted_at.asc())
        .all()
    )
    synced = 0
    for r in responses:
        answers_by_q = {a.question_id: a for a in r.answers}
        row = [r.submitted_at.strftime("%Y-%m-%d %H:%M:%S"), r.student.name, r.student.student_id]
        for q in questions:
            a = answers_by_q.get(q.id)
            if not a:
                row.append("")
            elif a.value_json:
                row.append(", ".join(a.value_json))
            else:
                row.append(a.value or "")
        append_row(survey.sheet_id, survey.sheet_tab or "Sheet1", row)
        r.synced_to_sheet = True
        synced += 1

    db.commit()
    return {"synced": synced}
