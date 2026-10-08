from datetime import date
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table as ExcelTable
from openpyxl.worksheet.table import TableStyleInfo

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


def _wrapped_lines(text, width):
    return sum(
        max(1, -(-_display_width(chunk) // max(1, int(width * 0.9))))
        for chunk in str(text or "").split("\n")
    )


def build(data: Table) -> bytes:
    data = Table.model_validate(data)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    workbook.properties.title = safe_text(data.title)
    workbook.properties.creator = "Telegram Services"

    columns = [safe_text(column) for column in data.columns]
    rows = [[cell_safe(value) for value in row] for row in data.rows]

    probe = " ".join(columns) + " " + " ".join(str(value) for value in (rows[0] if rows else []))
    rtl = is_rtl(probe)
    sheet.sheet_view.rightToLeft = rtl
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.sheet_properties.outlinePr.summaryRight = not rtl

    # The title is separate from the native sortable data table.
    sheet.append([safe_text(data.title)])
    sheet["A1"].data_type = "s"  # A title beginning with '=' is still customer text.
    sheet["A1"].font = Font(name="DejaVu Sans", bold=True, size=18, color="176B55")
    sheet["A1"].alignment = Alignment(
        horizontal="right" if rtl else "left", vertical="center", wrap_text=True
    )
    if len(columns) > 1:
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
    sheet.row_dimensions[1].height = 48
    sheet.append([])

    sheet.append(columns)
    for row in rows:
        sheet.append(row)

    header_align = Alignment(
        horizontal="right" if rtl else "left", vertical="center", wrap_text=True
    )
    # XML sanitation must not silently create duplicate/blank native table headers.
    if any(not c.strip() for c in columns) or len({c.casefold() for c in columns}) != len(columns):
        raise ValueError("invalid Excel table headers")
    for cell in sheet[3]:
        cell.data_type = "s"
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = header_align
    sheet.row_dimensions[3].height = 36

    for row in sheet.iter_rows(min_row=4):
        for cell in row:
            value = cell.value
            kind = data.column_formats[cell.column - 1].kind if data.column_formats else None
            if kind == "date" and value is not None:
                cell.value = date.fromisoformat(value)
                cell.number_format = "yyyy-mm-dd"
            elif kind == "percent" and value is not None:
                cell.number_format = "0.###############%"
            elif isinstance(value, str):
                cell.number_format = "@"
            elif _is_number(value):
                cell.number_format = (
                    "#,##0"
                    if isinstance(value, int)
                    else "0.##############E+00"
                    if value and abs(value) < 1e-10
                    else "#,##0.###############"
                )
            cell.font = BODY_FONT
            cell.border = BORDER
            if _is_number(value):
                horizontal = "right"
            elif isinstance(value, str) and is_rtl(value):
                horizontal = "right"
            else:
                horizontal = "left"
            cell.alignment = Alignment(
                horizontal=horizontal,
                vertical="top",
                wrap_text=True,
                readingOrder=2 if isinstance(value, str) and is_rtl(value) else 1,
            )

    widths = [_display_width(column) for column in columns]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], _display_width(value))
    for index, width in enumerate(widths, start=1):
        letter = get_column_letter(index)
        sheet.column_dimensions[letter].width = min(60, max(10, width + 2))
    title_width = sum(
        sheet.column_dimensions[get_column_letter(i)].width for i in range(1, len(columns) + 1)
    )
    sheet.row_dimensions[1].height = min(409, max(48, 25 * _wrapped_lines(data.title, title_width)))
    sheet.row_dimensions[3].height = min(
        409,
        max(
            36,
            16
            * max(
                _wrapped_lines(value, sheet.column_dimensions[get_column_letter(i)].width)
                for i, value in enumerate(columns, 1)
            )
            + 8,
        ),
    )

    for row in sheet.iter_rows(min_row=4):
        lines = 1
        for cell in row:
            text = "" if cell.value is None else str(cell.value)
            col_width = max(8, sheet.column_dimensions[get_column_letter(cell.column)].width or 8)
            lines = max(lines, _wrapped_lines(text, col_width))
        sheet.row_dimensions[row[0].row].height = min(409, max(22, 16 * lines + 6))

    last_column = get_column_letter(len(columns))
    ref = f"A3:{last_column}{sheet.max_row}"
    native_table = ExcelTable(displayName="Records", ref=ref)
    native_table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium4", showRowStripes=True, showColumnStripes=False
    )
    sheet.add_table(native_table)
    sheet.freeze_panes = "A4"
    sheet.auto_filter.ref = ref
    sheet.print_title_rows = "1:3"
    sheet.print_area = f"A1:{last_column}{sheet.max_row}"
    sheet.page_setup.orientation = "landscape" if len(columns) > 5 else "portrait"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A4
    sheet.page_setup.fitToWidth = 1 if len(columns) <= 8 else 0
    sheet.page_setup.fitToHeight = 0
    sheet.oddFooter.center.text = "&P / &N"
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
