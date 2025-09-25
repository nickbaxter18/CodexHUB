import pytest

from src.drive_client import DriveClient, DriveClientError, TokenStorage
from src.utils import TokenEncryptor


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

    token_storage = TokenStorage(tmp_path / "token.bin")
    client = DriveClient(str(creds), service_factory=factory, token_storage=token_storage)
    client.authenticate()
    folder_id = client.get_or_create_folder("News")
    file_id = client.upload_document(folder_id, "file.md", b"content")

    assert folder_id == "created-id"
    assert file_id == "created-id"
    assert service.files().created


def test_token_storage_roundtrip(tmp_path):
    storage_path = tmp_path / "token.enc"
    encryptor = TokenEncryptor.from_password("secret")
    storage = TokenStorage(storage_path, encryptor=encryptor)

    storage.save("token-value")
    assert storage_path.exists()
    assert storage.load() == "token-value"

    storage.clear()
    assert not storage_path.exists()


def test_drive_client_token_helpers(tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    storage = TokenStorage(tmp_path / "token.bin")

    client = DriveClient(str(creds), service_factory=service_factory, token_storage=storage)
    client.authenticate()

    assert client.load_token() is None
    client.store_token("abc")
    assert storage.load() == "abc"

    client.clear_token()
    assert storage.load() is None
