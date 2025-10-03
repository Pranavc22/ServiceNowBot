import os
from typing import Union
from io import BytesIO
from docx import Document

class TranscriptReader:
    def __init__(self, file: BytesIO, ext: str):
        """
        file: BytesIO object of uploaded file
        ext: file extension (e.g., '.txt', '.docx')
        """
        self.file = file
        self.ext = ext.lower()

    def read(self) -> str:
        return self._read_file(self.file, self.ext)

    def _read_file(self, file_obj: BytesIO, ext: str) -> str:
        if ext in [".txt", ".md", ".rtf"]:
            content = file_obj.read()
            try:
                return content.decode("utf-8")
            except Exception:
                return content.decode("latin-1", errors="ignore")
        elif ext == ".docx":
            doc = Document(file_obj)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            raise ValueError(f"Unsupported file type: {ext}")