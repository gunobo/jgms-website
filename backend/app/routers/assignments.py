from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from app.assignment_utils import criterion_to_out, max_score
from app.auth import CurrentUser, require_student
from app.database import get_db
from app.models import Assignment, RubricCriterion, Submission
from app.schemas import AssignmentDetail, AssignmentListItem, GradeOut, MySubmissionOut, SubmissionOut
from app.storage import save_submission_file

router = APIRouter(
    prefix="/api/assignments", tags=["assignments"], dependencies=[Depends(require_student)]
)


def _base_query(db: Session):
    return db.query(Assignment).options(
        selectinload(Assignment.criteria).selectinload(RubricCriterion.items)
    )


@router.get("", response_model=list[AssignmentListItem])
def list_assignments(db: Session = Depends(get_db), user: CurrentUser = Depends(require_student)):
    assignments = (
        _base_query(db).filter(Assignment.is_published.is_(True)).order_by(Assignment.created_at.desc()).all()
    )
    result = []
    for a in assignments:
        submission = (
            db.query(Submission)
            .options(selectinload(Submission.grade))
            .filter(Submission.assignment_id == a.id, Submission.student_id == user.user_id)
            .first()
        )
        result.append(
            AssignmentListItem(
                id=a.id,
                title=a.title,
                description=a.description,
                is_published=a.is_published,
                created_at=a.created_at,
                max_score=max_score(a),
                already_submitted=submission is not None,
                my_score=submission.grade.total_score if submission and submission.grade else None,
            )
        )
    return result


@router.get("/{assignment_id}", response_model=AssignmentDetail)
def get_assignment(
    assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_student)
):
    assignment = (
        _base_query(db)
        .filter(Assignment.id == assignment_id, Assignment.is_published.is_(True))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과제를 찾을 수 없습니다.")
    return AssignmentDetail(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        is_published=assignment.is_published,
        sheet_id=None,
        rubric_sheet_tab=None,
        scores_sheet_tab=None,
        created_at=assignment.created_at,
        criteria=[criterion_to_out(c) for c in sorted(assignment.criteria, key=lambda c: c.order)],
        max_score=max_score(assignment),
    )


@router.get("/{assignment_id}/my-submission", response_model=MySubmissionOut)
def get_my_submission(
    assignment_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_student)
):
    submission = (
        db.query(Submission)
        .options(selectinload(Submission.grade))
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == user.user_id)
        .first()
    )
    if not submission:
        return MySubmissionOut()

    assignment = _base_query(db).filter(Assignment.id == assignment_id).first()
    pts = max_score(assignment) if assignment else 0

    grade_out = None
    if submission.grade:
        g = submission.grade
        grade_out = GradeOut(
            id=g.id,
            checked_item_ids=g.checked_item_ids or [],
            total_score=g.total_score,
            max_score=pts,
            comment=g.comment,
            graded_at=g.graded_at,
            graded_by_name=None,
        )

    return MySubmissionOut(
        submission=SubmissionOut(
            id=submission.id,
            link_url=submission.link_url,
            text_content=submission.text_content,
            file_name=submission.file_name,
            submitted_at=submission.submitted_at,
            updated_at=submission.updated_at,
        ),
        grade=grade_out,
    )


@router.post("/{assignment_id}/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: str,
    link_url: str | None = Form(default=None),
    text_content: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_student),
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id, Assignment.is_published.is_(True))
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과제를 찾을 수 없습니다.")

    link_url = (link_url or "").strip() or None
    text_content = (text_content or "").strip() or None
    has_file = file is not None and file.filename

    if not link_url and not text_content and not has_file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="링크, 텍스트, 파일 중 최소 하나는 입력해주세요.",
        )

    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == user.user_id)
        .first()
    )
    if not submission:
        submission = Submission(assignment_id=assignment_id, student_id=user.user_id)
        db.add(submission)

    submission.link_url = link_url
    submission.text_content = text_content
    submission.updated_at = datetime.utcnow()

    if has_file:
        try:
            original_name, relative_path = await save_submission_file(assignment_id, user.user_id, file)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
        submission.file_name = original_name
        submission.file_path = relative_path

    db.commit()
    db.refresh(submission)

    return SubmissionOut(
        id=submission.id,
        link_url=submission.link_url,
        text_content=submission.text_content,
        file_name=submission.file_name,
        submitted_at=submission.submitted_at,
        updated_at=submission.updated_at,
    )
