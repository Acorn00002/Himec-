import csv

from app.services.parsing.types import Chunk


def _render_row(row: tuple) -> str | None:
    cells = ["" if v is None else str(v).strip() for v in row]
    if not any(cells):
        return None
    return " | ".join(cells)


def parse_xlsx(path: str) -> list[Chunk]:
    import openpyxl

    chunks: list[Chunk] = []
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        for sheet in wb.worksheets:
            lines = []
            for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                rendered = _render_row(row)
                if rendered:
                    lines.append(f"Row{row_index}: {rendered}")
            if lines:
                chunks.append(Chunk(location=sheet.title, content_type="table", text="\n".join(lines)))
    finally:
        wb.close()
    return chunks


def parse_csv(path: str) -> list[Chunk]:
    lines = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row_index, row in enumerate(csv.reader(f), start=1):
            rendered = _render_row(tuple(row))
            if rendered:
                lines.append(f"Row{row_index}: {rendered}")
    if not lines:
        return []
    return [Chunk(location="CSV", content_type="table", text="\n".join(lines))]
