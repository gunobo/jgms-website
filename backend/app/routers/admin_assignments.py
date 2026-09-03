from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.assignment_utils import all_items, criterion_to_out, max_score
from app.auth import CurrentUser, require_admin
from app.database import get_db
from app.models import Assignment, Grade, RubricCriterion, RubricItem, Submission
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
    append_row,
    extract_spreadsheet_id,
    is_sheets_configured,
    make_tab_name,
    write_header,
    write_rows,
)
from app.storage import resolve_upload_path

router = APIRouter(
    prefix="/api/admin/assignments", tags=["admin-assignments"], dependencies=[Depends(require_admin)]
)


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
        .order_by(Assignment.created_at.desc())
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
    assignment = Assignment(title=body.title, description=body.description, created_by_id=user.user_id)
    for ci, c in enumerate(body.criteria):
        criterion = RubricCriterion(title=c.title, description=c.description, order=ci)
        for ii, item in enumerate(c.items):
            criterion.items.append(RubricItem(label=item.label, points=item.points, order=ii))
        assignment.criteria.append(criterion)
    db.add(assignment)
    db.commit()
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


def _rubric_rows(assignment: Assignment) -> list[list[str]]:
    rows = [["평가 항목", "조건", "배점"]]
    for c in sorted(assignment.criteria, key=lambda c: c.order):
        for i in sorted(c.items, key=lambda i: i.order):
            rows.append([c.title, i.label, str(i.points)])
    rows.append(["", "총점", str(max_score(assignment))])
    return rows


@router.post("/{assignment_id}/sheet", response_model=AssignmentDetail)
def link_sheet(assignment_id: str, body: SheetLinkIn, db: Session = Depends(get_db)):
    if not is_sheets_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서버에 Google Sheets 서비스 계정이 설정되어 있지 않습니다.",
        )
    assignment = _get_assignment_or_404(db, assignment_id)
    sheet_id = extract_spreadsheet_id(body.sheet_url_or_id)
    rubric_tab = assignment.rubric_sheet_tab or make_tab_name(f"{assignment.title} 평가기준표", assignment.id)
    scores_tab = assignment.scores_sheet_tab or make_tab_name(f"{assignment.title} 점수", assignment.id)

    try:
        write_rows(sheet_id, rubric_tab, _rubric_rows(assignment))
        item_labels = [f"{c.title} - {i.label}" for c, i in all_items(assignment)]
        write_header(sheet_id, scores_tab, [*item_labels, "총점", "코멘트"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="스프레드시트에 연결할 수 없습니다. 시트를 서비스 계정과 공유했는지 확인해주세요.",
        ) from exc

    assignment.sheet_id = sheet_id
    assignment.rubric_sheet_tab = rubric_tab
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
        checked_item_ids=g.checked_item_ids or [],
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

    valid_item_ids = {i.id: i for _, i in all_items(assignment)}
    checked_ids = [iid for iid in body.checked_item_ids if iid in valid_item_ids]
    total = sum(valid_item_ids[iid].points for iid in checked_ids)

    if submission.grade:
        grade = submission.grade
        grade.checked_item_ids = checked_ids
        grade.total_score = total
        grade.comment = body.comment
        grade.graded_at = datetime.utcnow()
        grade.graded_by_id = user.user_id
        grade.synced_to_sheet = False
    else:
        grade = Grade(
            submission_id=submission.id,
            checked_item_ids=checked_ids,
            total_score=total,
            comment=body.comment,
            graded_by_id=user.user_id,
        )
        db.add(grade)
    db.commit()
    db.refresh(grade)

    if assignment.sheet_id:
        try:
            checked_set = set(checked_ids)
            row = [
                grade.graded_at.strftime("%Y-%m-%d %H:%M:%S"),
                submission.student.name,
                submission.student.student_id,
            ]
            for _, item in all_items(assignment):
                row.append("O" if item.id in checked_set else "")
            row.append(str(total))
            row.append(body.comment or "")
            append_row(assignment.sheet_id, assignment.scores_sheet_tab or "점수", row)
            grade.synced_to_sheet = True
            db.commit()
        except Exception:
            pass

    db.refresh(grade)
    pts = max_score(assignment)
    return _grade_to_out(grade, pts)
