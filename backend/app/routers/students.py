import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import RosterSheet, Student
from app.schemas import (
    RosterSheetOut,
    SheetLinkIn,
    SheetPreviewIn,
    SheetPreviewOut,
    StudentBulkCreate,
    StudentBulkResult,
    StudentCreate,
    StudentImportIn,
    StudentOut,
)
from app.sheets import (
    extract_spreadsheet_id,
    get_range_values,
    is_sheets_configured,
    unique_tab_name,
    write_rows,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/students", tags=["students"], dependencies=[Depends(require_admin)]
)


def _sync_roster_sheet(db: Session) -> None:
    """Best-effort: if a roster spreadsheet is linked, overwrite its tab with
    the current student list. Never raises — a sync failure shouldn't block
    roster edits."""
    roster_sheet = db.get(RosterSheet, "singleton")
    if not roster_sheet or not roster_sheet.sheet_id:
        return
    try:
        students = db.query(Student).order_by(Student.name.asc()).all()
        rows = [["이름", "학번", "이메일", "학년", "반"]]
        rows += [[s.name, s.student_id, s.email, s.grade or "", s.class_name or ""] for s in students]
        write_rows(roster_sheet.sheet_id, roster_sheet.sheet_tab or "학생 명단", rows)
    except Exception:
        pass


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.created_at.desc()).all()


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**body.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 학번 또는 이메일입니다."
        ) from exc
    db.refresh(student)
    _sync_roster_sheet(db)
    return student


@router.post("/bulk", response_model=StudentBulkResult)
def create_students_bulk(body: StudentBulkCreate, db: Session = Depends(get_db)):
    lines = [line.strip() for line in body.text.splitlines() if line.strip()]
    created = 0
    skipped: list[str] = []

    for line in lines:
        parts = [p.strip() for p in line.replace("\t", ",").split(",")]
        parts += [""] * (5 - len(parts))
        name, student_id, email, grade, class_name = parts[:5]

        try:
            data = StudentCreate(
                name=name,
                student_id=student_id,
                email=email,
                grade=grade or None,
                class_name=class_name or None,
            )
        except Exception:
            skipped.append(line)
            continue

        student = Student(**data.model_dump())
        db.add(student)
        try:
            db.commit()
            created += 1
        except IntegrityError:
            db.rollback()
            skipped.append(line)

    if created:
        _sync_roster_sheet(db)
    return StudentBulkResult(created=created, skipped=skipped)


@router.post("/sheet-preview", response_model=SheetPreviewOut)
def preview_sheet(body: SheetPreviewIn):
    if not is_sheets_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서버에 Google Sheets 서비스 계정이 설정되어 있지 않습니다.",
        )
    sheet_id = extract_spreadsheet_id(body.sheet_url_or_id)
    try:
        rows = get_range_values(sheet_id, body.range)
    except Exception as exc:
        logger.exception("Failed to preview sheet %s range %s", sheet_id, body.range)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"시트를 읽을 수 없습니다. 시트를 서비스 계정과 공유했는지, 범위가 맞는지 확인해주세요. ({exc})",
        ) from exc
    return SheetPreviewOut(rows=rows)


@router.post("/import", response_model=StudentBulkResult)
def import_students(body: StudentImportIn, db: Session = Depends(get_db)):
    created = 0
    skipped: list[str] = []

    for row in body.students:
        try:
            data = StudentCreate(
                name=row.name,
                student_id=row.student_id,
                email=row.email,
                grade=row.grade or None,
                class_name=row.class_name or None,
            )
        except Exception:
            skipped.append(f"{row.name},{row.student_id},{row.email}")
            continue

        student = Student(**data.model_dump())
        db.add(student)
        try:
            db.commit()
            created += 1
        except IntegrityError:
            db.rollback()
            skipped.append(f"{row.name},{row.student_id},{row.email}")

    if created:
        _sync_roster_sheet(db)
    return StudentBulkResult(created=created, skipped=skipped)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="학생을 찾을 수 없습니다.")
    db.delete(student)
    db.commit()
    _sync_roster_sheet(db)


@router.get("/sheet", response_model=RosterSheetOut)
def get_roster_sheet(db: Session = Depends(get_db)):
    roster_sheet = db.get(RosterSheet, "singleton")
    return RosterSheetOut(sheet_id=roster_sheet.sheet_id if roster_sheet else None)


@router.post("/sheet", response_model=RosterSheetOut)
def link_roster_sheet(body: SheetLinkIn, db: Session = Depends(get_db)):
    if not is_sheets_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="서버에 Google Sheets 서비스 계정이 설정되어 있지 않습니다.",
        )
    sheet_id = extract_spreadsheet_id(body.sheet_url_or_id)
    roster_sheet = db.get(RosterSheet, "singleton")
    if not roster_sheet:
        roster_sheet = RosterSheet(id="singleton")
        db.add(roster_sheet)

    try:
        tab = roster_sheet.sheet_tab or unique_tab_name(sheet_id, "학생 명단")
        students = db.query(Student).order_by(Student.name.asc()).all()
        rows = [["이름", "학번", "이메일", "학년", "반"]]
        rows += [[s.name, s.student_id, s.email, s.grade or "", s.class_name or ""] for s in students]
        write_rows(sheet_id, tab, rows)
        roster_sheet.sheet_id = sheet_id
        roster_sheet.sheet_tab = tab
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to link roster sheet %s", sheet_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"스프레드시트에 연결할 수 없습니다. 시트를 서비스 계정과 공유했는지 확인해주세요. ({exc})",
        ) from exc

    db.commit()
    return RosterSheetOut(sheet_id=sheet_id)


@router.delete("/sheet", response_model=RosterSheetOut)
def unlink_roster_sheet(db: Session = Depends(get_db)):
    roster_sheet = db.get(RosterSheet, "singleton")
    if roster_sheet:
        roster_sheet.sheet_id = None
        db.commit()
    return RosterSheetOut(sheet_id=None)
