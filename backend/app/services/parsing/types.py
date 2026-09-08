from dataclasses import dataclass


@dataclass
class Chunk:
    location: str
    content_type: str  # "text" | "table"
    text: str
