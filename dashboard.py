from flask import Flask, abort, send_from_directory
import os
from pathlib import Path

app = Flask(__name__)

ALLOWED_REELS_SUFFIXES = {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".wav", ".mp3", ".json", ".md"}
OUTPUTS_ROOT = Path("outputs").resolve()


@app.route('/images/generated/<path:filename>')
def generated_images(filename):
    return send_from_directory('images/generated', filename)


@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)


@app.route('/reels/outputs/<path:filename>')
def reels_outputs(filename):
    rel_path = Path(filename)
    if rel_path.suffix.lower() not in ALLOWED_REELS_SUFFIXES:
        abort(404)

    candidate = (OUTPUTS_ROOT / rel_path).resolve()
    try:
        candidate.relative_to(OUTPUTS_ROOT)
    except ValueError:
        abort(404)

    if not candidate.is_file():
        abort(404)

    return send_from_directory(str(OUTPUTS_ROOT), rel_path.as_posix())


if __name__ == "__main__":
    os.makedirs('images/generated', exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8082")))
