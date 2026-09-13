from dataclasses import asdict
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.db.session import get_session
from app.importers.classroom_students import (
    MAX_XLSX_SIZE_BYTES,
    ClassroomStudentImportValidationError,
    parse_classroom_students_xlsx,
)
from app.schemas.classroom_import import ClassroomStudentImportResult
from app.services.classroom_student_import import (
    ClassroomStudentImportConcurrentChangeError,
    ClassroomStudentImportRowConflictError,
    ClassroomStudentImportService,
    ImportClassroomInactiveError,
    ImportClassroomNotFoundError,
)

router = APIRouter(
    prefix="/classes/{classroom_id}/students",
    tags=["Classroom imports"],
)


@router.post(
    "/import",
    response_model=ClassroomStudentImportResult,
    status_code=status.HTTP_200_OK,
)
async def import_classroom_students(
    classroom_id: UUID,
    file: Annotated[
        UploadFile,
        File(description="Student list in .xlsx format"),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ClassroomStudentImportResult:
    try:
        if not file.filename or not file.filename.lower().endswith(".xlsx"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only .xlsx files are supported",
            )
        if file.size is not None and file.size > MAX_XLSX_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="The Excel file is larger than 5 MiB",
            )
        content = await file.read(MAX_XLSX_SIZE_BYTES + 1)
    finally:
        await file.close()

    if len(content) > MAX_XLSX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The Excel file is larger than 5 MiB",
        )

    try:
        rows = await run_in_threadpool(
            parse_classroom_students_xlsx,
            content,
        )

        service = ClassroomStudentImportService(session)

        return await service.import_students(
            classroom_id=classroom_id,
            rows=rows,
        )
    except ClassroomStudentImportValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "Invalid student spreadsheet",
                "issues": [asdict(issue) for issue in error.issues],
            },
        ) from error
    except ImportClassroomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        ) from error
    except ImportClassroomInactiveError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom is inactive",
        ) from error
    except ClassroomStudentImportRowConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "row number": error.row_number,
                "email": error.email,
                "message": error.message,
            },
        ) from error
    except ClassroomStudentImportConcurrentChangeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Import conflicts with the current database state"),
        ) from error
