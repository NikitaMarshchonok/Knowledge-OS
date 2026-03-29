from pathlib import Path

from app.services.parsers.base import BaseParser, ParsedDocument


class TextParser(BaseParser):
    supported_extensions = {".txt", ".md", ".log"}

    @staticmethod
    def supported_mime_types() -> set[str]:
        return {"text/plain"}

    def parse(self, path: Path) -> ParsedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return ParsedDocument(text=text)
