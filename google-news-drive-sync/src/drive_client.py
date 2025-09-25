"""Google Drive client wrapper for uploads."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class DriveClientError(RuntimeError):
    """Raised when Drive interactions fail."""


def _default_service_factory(credentials_path: str, scopes: list[str]):
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise DriveClientError(
            "Google API client libraries are required for Drive interactions."
        ) from exc

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=scopes,
    )
    return build("drive", "v3", credentials=credentials)


class DriveClient:
    """High-level helper around the Google Drive API."""

    def __init__(
        self,
        credentials_path: str,
        *,
        scopes: Optional[list[str]] = None,
        service_factory: Callable[[str, list[str]], Any] | None = None,
    ) -> None:
        self.credentials_path = credentials_path
        default_scope = "https://www.googleapis.com/auth/drive.file"
        self.scopes = scopes or [default_scope]
        factory = service_factory or _default_service_factory
        self._service_factory = factory
        self._service: Any | None = None

    def authenticate(self) -> None:
        logger.debug(
            "Authenticating with Google Drive using %s",
            self.credentials_path,
        )
        if not Path(self.credentials_path).exists():
            message = f"Credentials file not found: {self.credentials_path}"
            raise DriveClientError(message)
        self._service = self._service_factory(
            self.credentials_path,
            self.scopes,
        )

    @property
    def service(self) -> Any:
        if self._service is None:
            message = "Client not authenticated; call authenticate() first."
            raise DriveClientError(message)
        return self._service

    def get_or_create_folder(self, name: str) -> str:
        logger.info("Ensuring Drive folder '%s' exists", name)
        service = self.service
        files = service.files()
        query = " and ".join(
            [
                "mimeType = 'application/vnd.google-apps.folder'",
                "trashed = false",
                f"name = '{name}'",
            ]
        )
        response = files.list(q=query, fields="files(id, name)").execute()
        items = response.get("files", [])
        if items:
            folder_id = items[0]["id"]
            logger.debug("Found existing folder %s (%s)", name, folder_id)
            return folder_id

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = files.create(body=metadata, fields="id").execute()
        folder_id = folder["id"]
        logger.debug("Created folder %s (%s)", name, folder_id)
        return folder_id

    def upload_document(
        self,
        folder_id: str,
        filename: str,
        content: bytes,
        *,
        mime_type: str = "text/markdown",
    ) -> str:
        logger.info("Uploading %s to folder %s", filename, folder_id)
        service = self.service
        files = service.files()
        media_body = {
            "mimeType": mime_type,
            "body": content,
        }
        metadata: Dict[str, Any] = {
            "name": filename,
            "parents": [folder_id],
        }
        request = files.create(body=metadata, media_body=media_body, fields="id")
        created = request.execute()
        file_id = created["id"]
        logger.debug("Uploaded file %s (%s)", filename, file_id)
        return file_id
