# CLAUDE.md — Projekt-Richtlinien & Architektur

Diese Datei dient als kompakter Leitfaden für Entwickler, um die Architektur, Befehle und Code-Konventionen dieser Notizen-API schnell zu verstehen.

---

## 🚀 Wichtige Terminal-Befehle

### 📦 Abhängigkeiten & Umgebung
- **Projekt-Setup & Sync:** `uv sync`
- **Paket hinzufügen:** `uv add <paketname>`

### 🖥️ Server starten
- **FastAPI Backend (Port 8000):** `uv run fastapi dev main.py`
- **Streamlit Frontend (Port 8501):** `uv run streamlit run frontend.py`

### 🧪 Tests ausführen
- **Alle Tests:** `uv run pytest -v`
- **Spezifische Validierungs-Tests:** `uv run pytest test_validation.py -v`

---

## 🏗️ System-Architektur

Das Projekt ist als leichtgewichtige Full-Stack-Anwendung konzipiert:

```text
my-first-api/
│
├── main.py                     # FastAPI Backend & SQLModel Datenbank-Modelle
├── frontend.py                 # Streamlit GUI für den Endnutzer
├── test_validation.py          # Pytest Suite für Pydantic-Eingabevalidierung
├── notes.db                    # Lokale SQLite-Datenbank (wird auto-generiert)
│
└── Exploration/
    └── class_based_decorator.py # Tag 6 Hausaufgabe: Custom Decorator Exploration