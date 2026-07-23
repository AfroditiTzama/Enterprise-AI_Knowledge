import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from knowledge_assistant.core.config import Settings


_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/octet-stream",
    "",
}
_SUSPICIOUS_PDF_MARKERS = (
    b"/JavaScript",
    b"/JS",
    b"/Launch",
    b"/EmbeddedFile",
    b"/RichMedia",
)


class DocumentFileValidator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def validate(
        self,
        *,
        original_filename: str,
        content_type: str | None,
        file_content: bytes,
    ) -> None:
        extension = Path(original_filename).suffix.lower()
        if extension not in _ALLOWED_EXTENSIONS:
            raise ValueError(
                "Unsupported document type. Supported file types are "
                "PDF, DOCX and TXT."
            )

        if len(file_content) > self._settings.max_upload_bytes:
            megabytes = self._settings.max_upload_bytes / (1024 * 1024)
            raise ValueError(
                f"The uploaded file exceeds the {megabytes:.0f} MB limit."
            )

        normalized_type = (
            content_type.split(";", 1)[0].strip().lower()
            if content_type
            else ""
        )
        if normalized_type not in _ALLOWED_CONTENT_TYPES:
            raise ValueError("The uploaded MIME type is not allowed.")

        self._validate_signature(extension, file_content)

        if extension == ".pdf":
            self._validate_pdf_markers(file_content)

        if self._settings.clamav_enabled:
            await asyncio.to_thread(
                self._scan_with_clamav,
                original_filename,
                file_content,
            )

    @staticmethod
    def _validate_signature(extension: str, content: bytes) -> None:
        if extension == ".pdf" and not content.startswith(b"%PDF-"):
            raise ValueError("The file extension does not match a valid PDF.")
        if extension == ".docx" and not content.startswith(b"PK"):
            raise ValueError("The file extension does not match a valid DOCX.")
        if extension == ".txt" and b"\x00" in content[:4096]:
            raise ValueError("The TXT file appears to contain binary data.")

    @staticmethod
    def _validate_pdf_markers(content: bytes) -> None:
        sample = content[: min(len(content), 5_000_000)]
        detected = [
            marker.decode("ascii", errors="ignore")
            for marker in _SUSPICIOUS_PDF_MARKERS
            if marker in sample
        ]
        if detected:
            raise ValueError(
                "The PDF contains active or embedded content that is not "
                "accepted for security reasons."
            )

    def _scan_with_clamav(
        self,
        original_filename: str,
        file_content: bytes,
    ) -> None:
        command = self._settings.clamav_command
        if shutil.which(command) is None:
            raise ValueError(
                "Antivirus scanning is enabled, but the ClamAV command "
                "is not installed."
            )

        suffix = Path(original_filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix) as temporary:
            temporary.write(file_content)
            temporary.flush()
            result = subprocess.run(
                [command, "--no-summary", temporary.name],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        if result.returncode == 1:
            raise ValueError("The uploaded file failed the antivirus scan.")
        if result.returncode not in {0, 1}:
            raise ValueError("The antivirus scanner could not inspect the file.")
