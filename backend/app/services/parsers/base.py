from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedDocument:
    text: str
    page_count: int | None = None


class BaseParser:
    supported_extensions: set[str] = set()

    def can_parse(self, path: Path, mime_type: str | None = None) -> bool:
        extension = path.suffix.lower()
        if extension in self.supported_extensions:
            return True
        if mime_type is None:
            return False
        return mime_type in self.supported_mime_types()

    @staticmethod
    def supported_mime_types() -> set[str]:
        return set()

    def parse(self, path: Path) -> ParsedDocument:
        raise NotImplementedError
