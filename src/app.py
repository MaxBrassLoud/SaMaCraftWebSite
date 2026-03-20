from flask import Flask, render_template, jsonify, send_from_directory, abort
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
    # Nur die neuesten 2 News für die Vorschau auf der Startseite
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
    """Gibt alle News als JSON zurück."""
    return jsonify(load_news())


@app.route("/api/news/<news_id>")
def api_news_single(news_id):
    """Gibt eine einzelne News als JSON zurück."""
    for item in load_news():
        if item["id"] == news_id:
            return jsonify(item)
    abort(404)


@app.route("/api/news/download/<filename>")
def download_news_file(filename):
    """Stellt eine Datei zum Download bereit."""
    # Sicherheitscheck: Nur Dateien aus dem news_files-Verzeichnis
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(NEWS_FILES_DIR, safe_filename)

    if not os.path.exists(filepath):
        abort(404)

    return send_from_directory(
        NEWS_FILES_DIR,
        safe_filename,
        as_attachment=True
    )


# ─── Static Files ─────────────────────────────────────────────────────────────

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static"), filename)


if __name__ == "__main__":
    print("SaMaCraft Backend gestartet auf http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
