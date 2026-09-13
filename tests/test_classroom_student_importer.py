from io import BytesIO

import pytest
from openpyxl import Workbook

from app.importers.classroom_students import (
    ClassroomStudentImportValidationError,
    parse_classroom_students_xlsx,
)

pytestmark = pytest.mark.unit


def build_xlsx(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.worksheets[0]

    for row in rows:
        worksheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    return buffer.getvalue()


def test_parse_classroom_students_xlsx() -> None:
    content = build_xlsx(
        [
            [" full_name ", " EMAIL "],
            [
                " Alex Student ",
                " Alex.Student@Example.COM ",
            ],
            [
                "Maria Student",
                "maria.student@example.com",
            ],
        ]
    )

    rows = parse_classroom_students_xlsx(content)

    assert len(rows) == 2
    assert rows[0].row_number == 2
    assert rows[0].full_name == "Alex Student"
    assert str(rows[0].email) == ("alex.student@example.com")
    assert rows[1].row_number == 3


def test_rejects_duplicate_emails_case_insensitively() -> None:
    content = build_xlsx(
        [
            ["full_name", "email"],
            ["First Student", "student@example.com"],
            ["Second Student", "STUDENT@example.com"],
        ]
    )

    with pytest.raises(ClassroomStudentImportValidationError) as error_info:
        parse_classroom_students_xlsx(content)

    issue = error_info.value.issues[0]

    assert issue.row_number == 3
    assert issue.column == "email"
    assert issue.message == "Email duplicates row 2"


def test_collects_multiple_row_validation_issues() -> None:
    content = build_xlsx(
        [
            ["full_name", "email"],
            ["", "not-an-email"],
            ["Valid Name", "also-not-an-email"],
        ]
    )

    with pytest.raises(ClassroomStudentImportValidationError) as error_info:
        parse_classroom_students_xlsx(content)

    locations = {(issue.row_number, issue.column) for issue in error_info.value.issues}

    assert locations == {
        (2, "full_name"),
        (2, "email"),
        (3, "email"),
    }


def test_rejects_missing_required_header() -> None:
    content = build_xlsx(
        [
            ["full_name"],
            ["Alex Student"],
        ]
    )

    with pytest.raises(ClassroomStudentImportValidationError) as error_info:
        parse_classroom_students_xlsx(content)

    issue = error_info.value.issues[0]

    assert issue.row_number == 1
    assert issue.column == "email"
    assert issue.message == "Required header is missing"


def test_rejects_formulas() -> None:
    content = build_xlsx(
        [
            ["full_name", "email"],
            [
                '=CONCAT("Alex", " Student")',
                "alex@example.com",
            ],
        ]
    )

    with pytest.raises(ClassroomStudentImportValidationError) as error_info:
        parse_classroom_students_xlsx(content)

    issue = error_info.value.issues[0]

    assert issue.row_number == 2
    assert issue.column == "full_name"
    assert issue.message == "Formulas are not allowed"


def test_rejects_invalid_xlsx() -> None:
    with pytest.raises(ClassroomStudentImportValidationError) as error_info:
        parse_classroom_students_xlsx(b"not an xlsx file")

    assert error_info.value.issues[0].message == (
        "The uploaded file is not a valid .xlsx workbook"
    )
