
import io

import app.web as web


def setup_test_app(tmp_path, monkeypatch):
    """Prépare une application isolée pour les tests."""
    upload_dir = tmp_path / "uploads"
    output_dir = tmp_path / "outputs"

    upload_dir.mkdir()
    output_dir.mkdir()

    monkeypatch.setattr(web, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(web, "OUTPUT_DIR", output_dir)

    web.app.config.update(
        TESTING=True,
        MAX_CONTENT_LENGTH=500 * 1024 * 1024,
    )

    return web.app.test_client(), output_dir


def test_homepage(monkeypatch, tmp_path):
    client, _ = setup_test_app(tmp_path, monkeypatch)

    response = client.get("/")

    assert response.status_code == 200


def test_rejects_missing_video(monkeypatch, tmp_path):
    client, _ = setup_test_app(tmp_path, monkeypatch)

    response = client.post("/api/generate")

    assert response.status_code == 400


def test_rejects_invalid_extension(monkeypatch, tmp_path):
    client, _ = setup_test_app(tmp_path, monkeypatch)

    response = client.post(
        "/api/generate",
        data={
            "video": (
                io.BytesIO(b"not a video"),
                "document.txt",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400


def test_generates_and_serves_video(
    monkeypatch, tmp_path
):
    client, output_dir = setup_test_app(
        tmp_path, monkeypatch
    )

    
    def fake_analyze_video(
        video_path,
        output_name="best_of.mp4",
        artifacts_dir=None,
        **kwargs,
    ):
        result = output_dir / output_name
        result.write_bytes(b"fake mp4 content")
        return str(result)


    monkeypatch.setattr(
        web, "analyze_video", fake_analyze_video
    )

    response = client.post(
        "/api/generate",
        data={
            "video": (
                io.BytesIO(b"fake input"),
                "test.mp4",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True

    preview = client.get(data["preview_url"])
    assert preview.status_code == 200
    assert preview.data == b"fake mp4 content"

    download = client.get(data["download_url"])
    assert download.status_code == 200
    assert "attachment" in download.headers.get(
        "Content-Disposition", ""
    )


def test_handles_analysis_error(
    monkeypatch, tmp_path
):
    client, _ = setup_test_app(tmp_path, monkeypatch)

    def failing_analysis(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(
        web, "analyze_video", failing_analysis
    )

    response = client.post(
        "/api/generate",
        data={
            "video": (
                io.BytesIO(b"fake input"),
                "test.mp4",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert "error" in response.get_json()
