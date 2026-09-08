import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.assignment_utils import criterion_to_out, max_score, resolve_selection, selected_item_by_criterion
from app.auth import CurrentUser, require_admin
from app.database import get_db
from app.models import Assignment, Grade, RosterSheet, RubricCriterion, RubricItem, Student, Submission
from app.schemas import (
    AssignmentCreateIn,
    AssignmentDetail,
    AssignmentListItem,
    GradeIn,
    GradeOut,
    SheetLinkIn,
    SubmissionOut,
    SubmissionWithGradeOut,
)
from app.sheets import (
    create_spreadsheet,
    extract_spreadsheet_id,
    is_sheets_configured,
    unique_tab_name,
    write_rows,
)
from app.storage import resolve_upload_path

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/assignments", tags=["admin-assignments"], dependencies=[Depends(require_admin)]
)


def _to_naive_utc(dt: datetime | None) -> datetime | None:
    """Normalizes an incoming (possibly timezone-aware) datetime to naive UTC,
    matching the naive-UTC convention used everywhere else in this app."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _get_assignment_or_404(db: Session, assignment_id: str) -> Assignment:
    assignment = (
        db.query(Assignment)
        .options(selectinload(Assignment.criteria).selectinload(RubricCriterion.items))
        .filter(Assignment.id == assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="과제를 찾을 수 없습니다.")
    return assignment


def _to_detail(a: Assignment) -> AssignmentDetail:
    return AssignmentDetail(
        id=a.id,
        title=a.title,
        description=a.description,
        is_published=a.is_published,
        due_at=a.due_at,
        sheet_id=a.sheet_id,
        rubric_sheet_tab=a.rubric_sheet_tab,
        scores_sheet_tab=a.scores_sheet_tab,
        created_at=a.created_at,
        criteria=[criterion_to_out(c) for c in sorted(a.criteria, key=lambda c: c.order)],
        max_score=max_score(a),
    )


@router.get("", response_model=list[AssignmentListItem])
def list_assignments(db: Session = Depends(get_db)):
    assignments = (
        db.query(Assignment)
        .options(selectinload(Assignment.criteria).selectinload(RubricCriterion.items))
        .order_by(Assignment.created_at.asc())
        .all()
    )
    result = []
    for a in assignments:
        count = db.query(Submission).filter(Submission.assignment_id == a.id).count()
        result.append(
            AssignmentListItem(
                id=a.id,
                title=a.title,
                description=a.description,
                is_published=a.is_published,
                due_at=a.due_at,
                created_at=a.created_at,
                max_score=max_score(a),
                submission_count=count,
            )
        )
    return result


@router.post("", response_model=AssignmentDetail, status_code=status.HTTP_201_CREATED)
def create_assignment(
    body: AssignmentCreateIn, db: Session = Depends(get_db), user: CurrentUser = Depends(require_admin)
):
    assignment = Assignment(
        title=body.title,
        description=body.description,
        due_at=_to_naive_utc(body.due_at),
        created_by_id=user.user_id,
    )
    for ci, c in enumerate(body.criteria):
        criterion = RubricCriterion(title=c.title, description=c.description, order=ci)
        for ii, item in enumerate(c.items):
            criterion.items.append(RubricItem(label=item.label, points=item.points, order=ii))
        assignment.criteria.append(criterion)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # Best-effort: automatically link a grading spreadsheet so the admin
    # doesn't have to do it by hand. Reuses the roster's spreadsheet (the
    # club's "main" sheet) if one is linked — new tabs for this assignment's
    # rubric/scores get added there. Falls back to creating a brand new,
    # dedicated spreadsheet only if no roster sheet exists yet. Never blocks
    # assignment creation.
    if is_sheets_configured():
        try:
            roster_sheet = db.get(RosterSheet, "singleton")
            if roster_sheet and roster_sheet.sheet_id:
                sheet_id = roster_sheet.sheet_id
            else:
                sheet_id = create_spreadsheet(f"{assignment.title} - 채점표", share_with_email=user.email)
            scores_tab = _write_score_sheet(db, assignment, sheet_id)
            assignment.sheet_id = sheet_id
            assignment.scores_sheet_tab = scores_tab
            db.commit()
            db.refresh(assignment)
        except Exception:
            logger.exception("Failed to auto-link grading sheet for assignment %s", assignment.id)
            db.rollback()
            db.refresh(assignment)

    return _to_detail(assignment)


@router.get("/{assignment_id}", response_model=AssignmentDetail)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    return _to_detail(_get_assignment_or_404(db, assignment_id))


@router.put("/{assignment_id}", response_model=AssignmentDetail)
def update_assignment(assignment_id: str, body: AssignmentCreateIn, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, assignment_id)
    assignment.title = body.title
    assignment.description = body.description
    assignment.due_at = _to_naive_utc(body.due_at)

    existing_criteria = {c.id: c for c in assignment.criteria}
    incoming_criterion_ids = {c.id for c in body.criteria if c.id}
    for cid, c in list(existing_criteria.items()):
        if cid not in incoming_criterion_ids:
            assignment.criteria.remove(c)

    for ci, c in enumerate(body.criteria):
        if c.id and c.id in existing_criteria:
            criterion = existing_criteria[c.id]
            criterion.title = c.title
            criterion.description = c.description
            criterion.order = ci

            existing_items = {i.id: i for i in criterion.items}
            incoming_item_ids = {i.id for i in c.items if i.id}
            for iid, item in list(existing_items.items()):
                if iid not in incoming_item_ids:
                    criterion.items.remove(item)
            for ii, item in enumerate(c.items):
                if item.id and item.id in existing_items:
                    target = existing_items[item.id]
                    target.label = item.label
                    target.points = item.points
                    target.order = ii
                else:
                    criterion.items.append(RubricItem(label=item.label, points=item.points, order=ii))
        else:
            criterion = RubricCriterion(title=c.title, description=c.description, order=ci)
            for ii, item in enumerate(c.items):
                criterion.items.append(RubricItem(label=item.label, points=item.points, order=ii))
            assignment.criteria.append(criterion)

    db.commit()
    db.refresh(assignment)
    return _to_detail(assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, assignment_id)
    db.delete(assignment)
    db.commit()


@router.post("/{assignment_id}/publish", response_model=AssignmentDetail)
def set_published(assignment_id: str, published: bool, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, assignment_id)
    assignment.is_published = published
    db.commit()
    db.refresh(assignment)
    return _to_detail(assignment)


def _write_score_sheet(db: Session, assignment: Assignment, sheet_id: str) -> str:
    """Overwrites the score tab with one row per student in the roster (not
    just those graded so far), keyed by student — so grading or re-grading
    someone updates their row in place instead of appending a duplicate."""
    scores_tab = assignment.scores_sheet_tab or unique_tab_name(sheet_id, f"{assignment.title} 점수")

    criteria = sorted(assignment.criteria, key=lambda c: c.order)
    header = ["이름", "학번", *[c.title for c in criteria], "총점", "코멘트", "채점 시각"]

    students = db.query(Student).order_by(Student.student_id.asc()).all()
    submissions = (
        db.query(Submission)
        .options(selectinload(Submission.grade))
        .filter(Submission.assignment_id == assignment.id)
        .all()
    )
    grade_by_student_id = {s.student_id: s.grade for s in submissions if s.grade}

    rows = [header]
    for student in students:
        grade = grade_by_student_id.get(student.id)
        if grade:
            chosen_by_criterion = selected_item_by_criterion(assignment, grade.selected_item_ids or [])
            row = [student.name, student.student_id]
            for c in criteria:
                item = chosen_by_criterion.get(c.id)
                row.append(f"{item.label} ({item.points}점)" if item else "")
            row += [
                str(grade.total_score),
                grade.comment or "",
                grade.graded_at.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        else:
            row = [student.name, student.student_id, *([""] * (len(criteria) + 3))]
        rows.append(row)

    write_rows(sheet_id, scores_tab, rows)
    return scores_tab


@router.post("/{assignment_id}/sheet", response_model=AssignmentDetail)
def link_sheet(assignment_id: str, body: SheetLinkIn, db: Session = Depends(get_db)):
    if not is_sheets_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서버에 Google Sheets 서비스 계정이 설정되어 있지 않습니다.",
        )
    assignment = _get_assignment_or_404(db, assignment_id)
    sheet_id = extract_spreadsheet_id(body.sheet_url_or_id)

    try:
        scores_tab = _write_score_sheet(db, assignment, sheet_id)
    except Exception as exc:
        logger.exception("Failed to link assignment sheet %s", sheet_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"스프레드시트에 연결할 수 없습니다. 시트를 서비스 계정과 공유했는지 확인해주세요. ({exc})",
        ) from exc

    assignment.sheet_id = sheet_id
    assignment.scores_sheet_tab = scores_tab
    db.commit()
    db.refresh(assignment)
    return _to_detail(assignment)


@router.delete("/{assignment_id}/sheet", response_model=AssignmentDetail)
def unlink_sheet(assignment_id: str, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, assignment_id)
    assignment.sheet_id = None
    db.commit()
    db.refresh(assignment)
    return _to_detail(assignment)


def _submission_to_out(s: Submission) -> SubmissionOut:
    return SubmissionOut(
        id=s.id,
        link_url=s.link_url,
        text_content=s.text_content,
        file_name=s.file_name,
        submitted_at=s.submitted_at,
        updated_at=s.updated_at,
    )


def _grade_to_out(g: Grade | None, max_pts: int) -> GradeOut | None:
    if not g:
        return None
    return GradeOut(
        id=g.id,
        selected_item_ids=g.selected_item_ids or [],
        total_score=g.total_score,
        max_score=max_pts,
        comment=g.comment,
        graded_at=g.graded_at,
        graded_by_name=g.graded_by.name or g.graded_by.email if g.graded_by else None,
    )


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionWithGradeOut])
def list_submissions(assignment_id: str, db: Session = Depends(get_db)):
    assignment = _get_assignment_or_404(db, assignment_id)
    submissions = (
        db.query(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.grade).selectinload(Grade.graded_by),
        )
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    pts = max_score(assignment)
    return [
        SubmissionWithGradeOut(
            submission=_submission_to_out(s),
            student_name=s.student.name,
            student_number=s.student.student_id,
            grade=_grade_to_out(s.grade, pts),
        )
        for s in submissions
    ]


@router.get("/{assignment_id}/submissions/{submission_id}/file")
def download_submission_file(assignment_id: str, submission_id: str, db: Session = Depends(get_db)):
    submission = (
        db.query(Submission)
        .filter(Submission.id == submission_id, Submission.assignment_id == assignment_id)
        .first()
    )
    if not submission or not submission.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="파일을 찾을 수 없습니다.")
    path = resolve_upload_path(submission.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path, filename=submission.file_name or path.name)


@router.post("/{assignment_id}/submissions/{submission_id}/grade", response_model=GradeOut)
def grade_submission(
    assignment_id: str,
    submission_id: str,
    body: GradeIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    assignment = _get_assignment_or_404(db, assignment_id)
    submission = (
        db.query(Submission)
        .options(selectinload(Submission.student), selectinload(Submission.grade))
        .filter(Submission.id == submission_id, Submission.assignment_id == assignment_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="제출물을 찾을 수 없습니다.")

    resolved_ids, total = resolve_selection(assignment, body.selected_item_ids)

    if submission.grade:
        grade = submission.grade
        grade.selected_item_ids = resolved_ids
        grade.total_score = total
        grade.comment = body.comment
        grade.graded_at = datetime.utcnow()
        grade.graded_by_id = user.user_id
        grade.synced_to_sheet = False
    else:
        grade = Grade(
            submission_id=submission.id,
            selected_item_ids=resolved_ids,
            total_score=total,
            comment=body.comment,
            graded_by_id=user.user_id,
        )
        db.add(grade)
    db.commit()
    db.refresh(grade)

    if assignment.sheet_id:
        try:
            _write_score_sheet(db, assignment, assignment.sheet_id)
            grade.synced_to_sheet = True
            db.commit()
        except Exception:
            logger.exception("Failed to sync grade to sheet for submission %s", submission.id)

    db.refresh(grade)
    pts = max_score(assignment)
    return _grade_to_out(grade, pts)
