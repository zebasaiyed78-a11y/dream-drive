from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_non_pdf_file_is_rejected():
    response = client.post(
        "/upload-tables",
        files={
            "file": (
                "sample.txt",
                b"This is not a PDF",
                "text/plain",
            )
        },
    )
    assert response.status_code == 400
