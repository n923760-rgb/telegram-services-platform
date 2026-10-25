from io import BytesIO

import pytest
from openpyxl import load_workbook

from app.builders import csv_review, excel


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["en", "ar"])
def test_review_print_preserves_data_and_wraps_all_audit_columns(language):
    content, _ = csv_review.build(
        ["ID", "Name", "Amount"], [["00123", "=1+1", "125.50"]], trim=True, language=language
    )
    book = load_workbook(BytesIO(content))
    assert book["Data"]["A4"].value == "00123"
    assert book["Data"]["B4"].data_type == "s"
    for name in ("Review", "Columns"):
        sheet = book[name]
        assert sheet.sheet_properties.pageSetUpPr.fitToPage
        assert sheet.page_setup.fitToWidth == 1
        assert sheet.page_setup.fitToHeight == 0
        assert not sheet.print_options.headings
        for cell in sheet[3]:
            lines = excel._wrapped_lines(
                cell.value, sheet.column_dimensions[cell.column_letter].width, bold=True
            )
            assert sheet.row_dimensions[3].height >= 11 * 1.6 * lines + 12
