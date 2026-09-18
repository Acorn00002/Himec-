import csv

from app.services.parsing.types import Chunk


def _render_row(row: tuple) -> str | None:
    cells = ["" if v is None else str(v).strip() for v in row]
    if not any(cells):
        return None
    return " | ".join(cells)


def _row_chunks(rows: list[tuple[int, str]], location_prefix: str) -> list[Chunk]:
    """Turn (row_index, rendered_row) pairs into one Chunk per data row, each carrying
    header/title context and a location that names the exact physical row (e.g. "Row3"
    or "Sheet1!Row3") — so a value the AI cites can be traced back to (and the UI can
    highlight) that one row instead of the whole table.

    Real sheets often start with a single-cell title/banner line before the actual
    column-header row (e.g. "△△ 프로젝트 - 부하 계산서 / EL-CALC-007 Rev.A"). The header
    is detected as the first row with more than one cell (rendered rows join cells with
    " | ", so a lone title line has zero " | " in it); any single-cell rows before it are
    kept as extra context rather than mistaken for the header or emitted as a fake data row.
    """
    if not rows:
        return []
    header_pos = next((i for i, (_, r) in enumerate(rows) if " | " in r), 0)
    context = "\n".join(r for _, r in rows[: header_pos + 1])
    chunks = []
    for row_index, rendered in rows[header_pos + 1:]:
        text = f"{context}\nRow{row_index}: {rendered}"
        chunks.append(Chunk(location=f"{location_prefix}Row{row_index}", content_type="table", text=text))
    return chunks


def parse_xlsx(path: str) -> list[Chunk]:
    import openpyxl

    chunks: list[Chunk] = []
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        multi_sheet = len(wb.worksheets) > 1
        for sheet in wb.worksheets:
            rows = []
            for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                rendered = _render_row(row)
                if rendered:
                    rows.append((row_index, rendered))
            prefix = f"{sheet.title}!" if multi_sheet else ""
            chunks.extend(_row_chunks(rows, prefix))
    finally:
        wb.close()
    return chunks


def parse_csv(path: str) -> list[Chunk]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row_index, row in enumerate(csv.reader(f), start=1):
            rendered = _render_row(tuple(row))
            if rendered:
                rows.append((row_index, rendered))
    return _row_chunks(rows, "")
