from app.services.parsing.types import Chunk


def parse_pdf(path: str) -> list[Chunk]:
    import pdfplumber

    chunks: list[Chunk] = []
    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(Chunk(location=f"p.{page_index}", content_type="text", text=text))

            for table_index, table in enumerate(page.extract_tables() or [], start=1):
                rows = [
                    " | ".join(cell.strip() if cell else "" for cell in row)
                    for row in table
                    if any(cell and cell.strip() for cell in row)
                ]
                if rows:
                    location = f"p.{page_index} (table {table_index})" if table_index > 1 else f"p.{page_index} (table)"
                    chunks.append(Chunk(location=location, content_type="table", text="\n".join(rows)))
    return chunks
