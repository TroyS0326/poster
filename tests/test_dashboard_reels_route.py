from pathlib import Path

import dashboard


def test_reels_route_rejects_path_traversal(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    monkeypatch.setattr(dashboard, "OUTPUTS_ROOT", outputs.resolve())

    client = dashboard.app.test_client()
    response = client.get("/reels/outputs/../outside.mp4")
    assert response.status_code == 404


def test_reels_route_serves_allowed_file(tmp_path, monkeypatch):
    outputs = tmp_path / "outputs"
    file_path = outputs / "queue/day_03/example/example.mp4"
    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"mp4")
    monkeypatch.setattr(dashboard, "OUTPUTS_ROOT", outputs.resolve())

    client = dashboard.app.test_client()
    response = client.get("/reels/outputs/queue/day_03/example/example.mp4")
    assert response.status_code == 200
    assert response.data == b"mp4"


def test_existing_image_route_still_works():
    client = dashboard.app.test_client()
    response = client.get("/images/generated/does_not_exist.jpg")
    assert response.status_code == 404
