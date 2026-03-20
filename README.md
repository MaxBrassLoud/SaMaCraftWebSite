# SaMaCraft Website – Python Backend

## Projektstruktur

```
samacraft/
├── app.py              ← Flask Backend (Hauptdatei)
├── news.json           ← News-Daten (hier bearbeitest du die News)
├── news_files/         ← Download-Dateien für News
│   ├── regelwerk_v1.txt
│   └── halloween_event.txt
├── static/
│   ├── style.css
│   └── script.js
└── templates/
    ├── index.html
    ├── news.html       ← dynamisch, lädt News per API
    ├── rules.html
    ├── team.html
    └── join.html
```

## Installation & Start

```bash
# 1. Abhängigkeiten installieren
pip install flask

# 2. Server starten
python app.py

# 3. Im Browser öffnen
http://localhost:5000
```

## News bearbeiten (news.json)

Jede News hat folgendes Format:

```json
{
  "id": "eindeutige-id",
  "type": "update",       ← update | changelog | event | info | alert
  "title": "Titel",
  "date": "2025-11-01",   ← Format: YYYY-MM-DD
  "content": "Text...",
  "download": null        ← null = kein Download
}
```

### Mit Download-Button:

```json
{
  "id": "meine-news",
  "type": "info",
  "title": "Wichtige Info",
  "date": "2025-11-10",
  "content": "Beschreibung...",
  "download": {
    "label": "Details herunterladen",
    "file": "dateiname.txt"
  }
}
```

Die Datei muss im Ordner `news_files/` liegen.

## API-Endpunkte

| Methode | URL                              | Beschreibung             |
|---------|----------------------------------|--------------------------|
| GET     | `/api/news`                      | Alle News als JSON       |
| GET     | `/api/news/<id>`                 | Einzelne News als JSON   |
| GET     | `/api/news/download/<dateiname>` | Datei herunterladen      |

## News-Typen & Farben

| Typ         | Farbe     | Verwendung                        |
|-------------|-----------|-----------------------------------|
| `update`    | 🟠 Orange | Server-Updates, neue Features     |
| `changelog` | 🔵 Blau   | Technische Änderungen             |
| `event`     | 🟣 Lila   | Events, Aktionen                  |
| `info`      | 🟢 Grün   | Allgemeine Informationen          |
| `alert`     | 🔴 Rot    | Warnungen, Wartung, Wichtiges     |
