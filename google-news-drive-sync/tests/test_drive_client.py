import pytest

from src.drive_client import DriveClient, DriveClientError


class FakeFiles:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.created = []

    def list(self, **kwargs):
        response = {"files": self.existing}

        class _Exec:
            def execute(self_inner):
                return response

        return _Exec()

    def create(self, **kwargs):
        class _Exec:
            def __init__(self_inner, created, payload):
                self_inner._created = created
                self_inner._payload = payload

            def execute(self_inner):
                file_id = "created-id"
                self_inner._created.append({"id": file_id, **self_inner._payload["body"]})
                return {"id": file_id}

        return _Exec(self.created, kwargs)


def make_service(existing=None):
    files = FakeFiles(existing=existing)

    class FakeService:
        def files(self_inner):
            return files

    return FakeService()


def service_factory(credentials_path, scopes):
    return make_service()


def test_drive_client_authentication_requires_credentials(tmp_path):
    client = DriveClient(str(tmp_path / "missing.json"), service_factory=service_factory)
    with pytest.raises(DriveClientError):
        client.authenticate()


def test_drive_client_reuses_existing_folder(tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    existing = [{"id": "folder-id", "name": "News"}]

    def factory(path, scopes):
        assert path == str(creds)
        return make_service(existing=existing)

    client = DriveClient(str(creds), service_factory=factory)
    client.authenticate()
    folder_id = client.get_or_create_folder("News")

    assert folder_id == "folder-id"


def test_drive_client_creates_folder_and_uploads(tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    service = make_service()

    def factory(path, scopes):
        return service

    client = DriveClient(str(creds), service_factory=factory)
    client.authenticate()
    folder_id = client.get_or_create_folder("News")
    file_id = client.upload_document(folder_id, "file.md", b"content")

    assert folder_id == "created-id"
    assert file_id == "created-id"
    assert service.files().created
