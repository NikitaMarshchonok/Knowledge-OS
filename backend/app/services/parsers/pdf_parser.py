from pathlib import Path

from pypdf import PdfReader

from app.services.parsers.base import BaseParser, ParsedDocument


class PdfParser(BaseParser):
    supported_extensions = {".pdf"}

    @staticmethod
    def supported_mime_types() -> set[str]:
        return {"application/pdf"}

    def parse(self, path: Path) -> ParsedDocument:
        reader = PdfReader(str(path))
        pages: list[str] = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        text = "\n\n".join(pages)
        return ParsedDocument(text=text, page_count=len(reader.pages))
