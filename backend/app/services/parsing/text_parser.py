from app.services.parsing.types import Chunk


def parse_txt(path: str) -> list[Chunk]:
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read().strip()
    if not text:
        return []
    return [Chunk(location="전체", content_type="text", text=text)]
