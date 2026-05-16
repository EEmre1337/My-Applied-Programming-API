# Notizen REST API
## Angewandte Programmierung · Hochschule Coburg

Alle Kurstag-Endpoints sind in einer einzigen FastAPI-App (`main.py`) gebündelt, ergänzt durch ein Streamlit-Frontend (`frontend.py`) und eine umfangreiche Pytest-Test-Suite.

---

## 🛠️ Setup & Entwicklung

**Abhängigkeiten installieren**
```bash
uv sync
```

**Backend starten**
```bash
uv run fastapi dev main.py
# → http://127.0.0.1:8000
# → Swagger-Doku: http://127.0.0.1:8000/docs
```

**Frontend starten** (separates Terminal)
```bash
uv run streamlit run frontend.py
# → http://localhost:8501
```

**Tests ausführen**
```bash
# Alle Tests (kein laufender Server nötig)
uv run pytest -v

# Nur TestClient-Suite
uv run pytest Exploration/test_main.py -v

# Einzelner Test
uv run pytest Exploration/test_main.py::test_read_root -v

# Validierungs-Tests
uv run pytest Exploration/test_validation.py -v
```

> Die Integrations-Tests in `Exploration/test_suit.py` schicken echte HTTP-Requests an `http://127.0.0.1:8000` und überspringen sich automatisch (via `_require_server`-Fixture), wenn der Server nicht läuft.

---

## 📁 Projektstruktur

```
my-first-api/
├── main.py                        # Komplette FastAPI-App (alle Kurstage)
├── frontend.py                    # Streamlit-Frontend für die Notes-API
├── notes.db                       # SQLite-Datenbank (via SQLModel)
├── CLAUDE.md                      # Architektur-Dokumentation
├── work-log.md                    # Lerntagebuch (Days 1–9)
├── pyproject.toml                 # Projektabhängigkeiten
├── uv.lock                        # Lockfile
├── data/
│   └── notes.json                 # Legacy JSON-Persistenz (Day 2, historisch)
└── Exploration/
    ├── class_based_decorator.py   # Decorator-Lernartefakt (Day 6)
    ├── test_main.py               # Haupt-Test-Suite (TestClient + Integration)
    ├── test_suit.py               # Referenz-Test-Suite (requests-basiert)
    └── test_validation.py         # Pydantic-Validierungs-Tests (Day 5)
```

---

## 🏛️ API-Übersicht

### Notes (Day 2–5)

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| `POST` | `/notes` | Neue Notiz erstellen (201) |
| `GET` | `/notes` | Alle Notizen (mit Filtern: `category`, `search`, `tag`, `created_after`, `created_before`) |
| `GET` | `/notes/stats` | Statistiken (total, by_category, top_tags) |
| `GET` | `/notes/{id}` | Einzelne Notiz |
| `PUT` | `/notes/{id}` | Vollständige Ersetzung |
| `PATCH` | `/notes/{id}` | Partielle Aktualisierung |
| `DELETE` | `/notes/{id}` | Löschen (204) |
| `DELETE` | `/notes/duplicates` | Duplikate entfernen |

### Kategorien & Tags

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| `GET` | `/categories` | Alle genutzten Kategorien |
| `GET` | `/categories/{name}/notes` | Notizen einer Kategorie |
| `GET` | `/tags` | Alle genutzten Tags |
| `GET` | `/tags/{name}/notes` | Notizen mit einem Tag |

### Weitere Endpoints (Day 3–4)

| Method | Endpoint | Beschreibung |
|--------|----------|-------------|
| `GET` | `/` | Hello World |
| `GET` | `/greetings/{name}` | Personalisierte Begrüßung |
| `GET` | `/is-adult/{age}` | Volljährigkeitsprüfung |
| `GET` | `/queryparameters` | Query-Parameter-Demo |

---

## 🗄️ Datenbankdesign

Die App nutzt **SQLite** über **SQLModel** (Pydantic + SQLAlchemy). Tags werden als CSV-String in einer `tags`-Spalte gespeichert (SQLite kennt keinen Array-Typ) und an den API-Grenzen über `_tags_to_csv` / `_tags_to_list` konvertiert — nach außen liefert die API immer eine saubere `list[str]`.

**Kritische Route-Reihenfolge:** `/notes/stats` und `/notes/duplicates` müssen **vor** `/notes/{note_id}` definiert sein, da FastAPI Top-Down matched und sonst `stats`/`duplicates` als Integer-Path-Parameter interpretiert.

---

## ✅ Pydantic-Validierung (Day 5)

`NoteCreate` und `NoteUpdate` erzwingen:

- `title`: 3–100 Zeichen (nach Strip)
- `content`: 1–10.000 Zeichen
- `category`: muss in `{work, personal, school, ideas, general}` sein, wird normalisiert (lowercase)
- `tags`: max. 10 Tags, jeder 2–30 Zeichen, Pattern `^[a-z0-9-]+$`, automatisch dedupliziert
- `extra="forbid"`: unbekannte Felder (Tippfehler) werden mit 422 abgelehnt
- `str_strip_whitespace=True`: Whitespace wird automatisch entfernt

---

## 🧪 Testen

- **`Exploration/test_main.py`** — Haupt-Suite mit `TestClient` (kein Server nötig) + Faker für Testdaten. Die `clean_notes`-Fixture leitet die SQLite-Engine per `monkeypatch` auf eine temporäre DB um.
- **`Exploration/test_suit.py`** — Referenz-Suite mit `requests` (Server muss laufen), auto-skip via `_require_server`-Fixture.
- **`Exploration/test_validation.py`** — Validierungs-Tests für Pydantic-Constraints.

---

## 📚 Technologie-Stack

| Technologie | Version | Verwendung |
|-------------|---------|-----------|
| Python | 3.13 | Laufzeitumgebung |
| FastAPI | ≥ 0.136 | Web-Framework |
| SQLModel | ≥ 0.0.38 | ORM + Pydantic-Integration |
| Pydantic | ≥ 2.13 | Datenvalidierung |
| Streamlit | ≥ 1.57 | Frontend |
| pytest | ≥ 9.0 | Testing |
| uv | — | Paketmanagement |