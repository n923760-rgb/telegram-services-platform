from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.builders.schema import Table
from app.builders.word import safe_text


def cell_safe(value):
    if isinstance(value, str):
        value = safe_text(value)
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def build(data: Table) -> bytes:
    data = Table.model_validate(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.sheet_view.rightToLeft = True
    sheet.append([cell_safe(c) for c in data.columns])
    for row in data.rows:
        sheet.append([cell_safe(v) for v in row])
    for cell in sheet[1]:
        cell.font = Font(name="DejaVu Sans", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="176B55")
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal="right", vertical="top", wrap_text=True)
    for index in range(1, len(data.columns) + 1):
        width = max(
            len(str(sheet.cell(row, index).value or "")) for row in range(1, sheet.max_row + 1)
        )
        sheet.column_dimensions[get_column_letter(index)].width = min(60, max(12, width + 2))
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
