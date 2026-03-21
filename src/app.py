from flask import Flask, render_template, jsonify, send_from_directory, abort, request
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_FILE = os.path.join(BASE_DIR, "news.json")
NEWS_FILES_DIR = os.path.join(BASE_DIR, "news_files")


def load_news():
    """Lädt News aus der JSON-Datei."""
    if not os.path.exists(NEWS_FILE):
        return []
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Seiten ───────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/index.html")
def index():
    news = load_news()
    preview = news[:2]
    return render_template("index.html", news_preview=preview)


@app.route("/news")
@app.route("/news.html")
def news():
    news_list = load_news()
    return render_template("news.html", news_list=news_list)


@app.route("/rules.html")
def rules():
    return render_template("rules.html")


@app.route("/team.html")
def team():
    return render_template("team.html")


@app.route("/join.html")
def join():
    return render_template("join.html")


# ─── API ──────────────────────────────────────────────────────────────────────

@app.route("/api/news")
def api_news():
    return jsonify(load_news())


@app.route("/api/news/<news_id>")
def api_news_single(news_id):
    for item in load_news():
        if item["id"] == news_id:
            return jsonify(item)
    abort(404)


@app.route("/api/news/download/<filename>")
def download_news_file(filename):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(NEWS_FILES_DIR, safe_filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_from_directory(NEWS_FILES_DIR, safe_filename, as_attachment=True)


# ─── Static Files ─────────────────────────────────────────────────────────────

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)


# ─── Error Handler ────────────────────────────────────────────────────────────

@app.errorhandler(400)
def bad_request(e):
    if request.path.startswith("/api/"):
        return jsonify(error="400 Bad Request", message=str(e)), 400
    return render_template("errors/400.html"), 400

@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith("/api/"):
        return jsonify(error="403 Forbidden", message=str(e)), 403
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify(error="404 Not Found", message=str(e)), 404
    return render_template("errors/404.html"), 404

@app.errorhandler(405)
def method_not_allowed(e):
    if request.path.startswith("/api/"):
        return jsonify(error="405 Method Not Allowed", message=str(e)), 405
    return render_template("errors/405.html"), 405

@app.errorhandler(429)
def too_many_requests(e):
    if request.path.startswith("/api/"):
        return jsonify(error="429 Too Many Requests", message=str(e)), 429
    return render_template("errors/429.html"), 429

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith("/api/"):
        return jsonify(error="500 Internal Server Error", message=str(e)), 500
    return render_template("errors/500.html"), 500

@app.errorhandler(503)
def service_unavailable(e):
    if request.path.startswith("/api/"):
        return jsonify(error="503 Service Unavailable", message=str(e)), 503
    return render_template("errors/503.html"), 503


# ─── Test-Routen (nur im Debug-Modus aktiv lassen) ────────────────────────────
# Zum Testen der Fehlerseiten: /test/404, /test/500 etc.
@app.route("/test/<int:code>")
def test_error(code):
    abort(code)


if __name__ == "__main__":
    print("SaMaCraft Backend gestartet auf http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)