from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.builders.direction import is_rtl
from app.builders.schema import Table
from app.builders.word import safe_text

HEADER_FILL = PatternFill("solid", fgColor="176B55")
HEADER_FONT = Font(name="DejaVu Sans", bold=True, color="FFFFFF")
BODY_FONT = Font(name="DejaVu Sans")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def cell_safe(value):
    if isinstance(value, str):
        value = safe_text(value)
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def _display_width(value):
    text = "" if value is None else str(value)
    return sum(2 if ord(char) > 0x2E7F else 1 for char in text)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def build(data: Table) -> bytes:
    data = Table.model_validate(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    workbook.properties.title = safe_text(data.title)

    columns = [safe_text(column) for column in data.columns]
    rows = [[cell_safe(value) for value in row] for row in data.rows]

    probe = " ".join(columns) + " " + " ".join(str(value) for value in (rows[0] if rows else []))
    rtl = is_rtl(probe)
    sheet.sheet_view.rightToLeft = rtl

    sheet.append(columns)
    for row in rows:
        sheet.append(row)

    header_align = Alignment(
        horizontal="right" if rtl else "left", vertical="center", wrap_text=True
    )
    for cell in sheet[1]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = header_align
    sheet.row_dimensions[1].height = 24

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            value = cell.value
            cell.font = BODY_FONT
            cell.border = BORDER
            if _is_number(value):
                horizontal = "right"
            elif isinstance(value, str) and is_rtl(value):
                horizontal = "right"
            else:
                horizontal = "left"
            cell.alignment = Alignment(horizontal=horizontal, vertical="top", wrap_text=True)

    widths = [_display_width(column) for column in columns]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], _display_width(value))
    for index, width in enumerate(widths, start=1):
        letter = get_column_letter(index)
        sheet.column_dimensions[letter].width = min(60, max(10, width + 2))

    for row in sheet.iter_rows(min_row=2):
        lines = 1
        for cell in row:
            text = "" if cell.value is None else str(cell.value)
            col_width = max(8, sheet.column_dimensions[get_column_letter(cell.column)].width or 8)
            wrapped = 0
            for chunk in text.split("\n"):
                wrapped += max(1, -(-_display_width(chunk) // int(col_width * 1.1)))
            lines = max(lines, wrapped)
        sheet.row_dimensions[row[0].row].height = min(120, max(18, 15 * lines + 4))

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
