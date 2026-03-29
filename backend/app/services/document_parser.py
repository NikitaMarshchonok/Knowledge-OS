from pathlib import Path

from app.services.parsers.base import BaseParser, ParsedDocument
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.tabular_parser import TabularParser
from app.services.parsers.text_parser import TextParser


class UnsupportedDocumentTypeError(Exception):
    pass


class DocumentParserService:
    def __init__(self) -> None:
        self.parsers: list[BaseParser] = [PdfParser(), DocxParser(), TabularParser(), TextParser()]

    def parse_document(self, file_path: str, mime_type: str | None = None) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        parser = self._select_parser(path, mime_type)
        if parser is None:
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type for '{path.name}'. Supported: txt, pdf, docx, csv, xlsx"
            )

        return parser.parse(path)

    def _select_parser(self, path: Path, mime_type: str | None = None) -> BaseParser | None:
        for parser in self.parsers:
            if parser.can_parse(path, mime_type):
                return parser
        return None
