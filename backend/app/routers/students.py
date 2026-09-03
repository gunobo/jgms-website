from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Student
from app.schemas import StudentBulkCreate, StudentBulkResult, StudentCreate, StudentOut

router = APIRouter(
    prefix="/api/admin/students", tags=["students"], dependencies=[Depends(require_admin)]
)


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

    return StudentBulkResult(created=created, skipped=skipped)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="학생을 찾을 수 없습니다.")
    db.delete(student)
    db.commit()
