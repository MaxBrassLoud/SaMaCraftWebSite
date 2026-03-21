"""
start.py – Startet Flask-Webserver und Discord-Bot gleichzeitig.
Einfach ausführen: python start.py
"""

import threading
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── Pfade ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, ""))


# ─── Flask in eigenem Thread ──────────────────────────────────────────────────
def run_flask():
    from app import app

    host  = os.getenv("FLASK_HOST",  "0.0.0.0")
    port  = int(os.getenv("FLASK_PORT",  "8880"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print(f"🌐 Flask startet auf http://{host}:{port}  (debug={debug})")
    # use_reloader=False ist wichtig, damit Flask nicht doppelt startet
    app.run(host=host, port=port, debug=debug, use_reloader=False)


# ─── Discord Bot im Hauptthread ───────────────────────────────────────────────
def run_bot():
    # Importiere bot aus bot.py im Projektroot
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "bot", pathlib.Path(BASE_DIR) / "bot.py"
    )
    bot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot_module)

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ DISCORD_BOT_TOKEN fehlt in der .env Datei!")
        sys.exit(1)

    print("🤖 Discord Bot startet…")
    bot_module.bot.run(token)


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Flask in Hintergrund-Thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Discord Bot blockiert den Hauptthread (asyncio-Loop)
    run_bot()