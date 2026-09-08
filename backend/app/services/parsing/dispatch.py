from app.services.parsing.pdf_parser import parse_pdf
from app.services.parsing.spreadsheet_parser import parse_csv, parse_xlsx
from app.services.parsing.text_parser import parse_txt
from app.services.parsing.types import Chunk

# doc_type -> deterministic parser. "image" has no entry here — there is nothing to
# deterministically extract from a photo/scan; Phase 9 reads image files directly
# with Gemini's vision input instead of chunk text.
PARSERS = {
    "pdf": parse_pdf,
    "xlsx": parse_xlsx,
    "csv": parse_csv,
    "txt": parse_txt,
}


def parse_document(doc_type: str, path: str) -> list[Chunk]:
    parser = PARSERS.get(doc_type)
    if parser is None:
        return []
    return parser(path)
