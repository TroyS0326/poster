from flask import Flask, send_from_directory
import os

app = Flask(__name__)


@app.route('/images/generated/<path:filename>')
def generated_images(filename):
    return send_from_directory('images/generated', filename)


@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('images', filename)


if __name__ == "__main__":
    os.makedirs('images/generated', exist_ok=True)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
