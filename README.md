# Notizen REST API
## Angewandte Programmierung · Hochschule Coburg

Eine vollständige REST API für Notizen, gebaut mit **FastAPI** und **SQLite**, ergänzt durch ein **Streamlit-Frontend** und eine eigene **Pytest-Test-Suite**.

---

## 🛠️ Setup & Entwicklung

**Abhängigkeiten installieren**
```bash
uv sync
```

**Backend starten**
```bash
uv run fastapi dev main.py
# → API:          http://127.0.0.1:8000
# → Swagger Docs: http://127.0.0.1:8000/docs
```

**Frontend starten** *(separates Terminal)*
```bash
uv run streamlit run frontend.py
# → http://localhost:8501
```

---

## 🧪 Tests ausführen

Beide Test-Suites benötigen ein laufendes Backend (Terminal 1: Server, Terminal 2: Tests).

```bash
# Eigene Pydantic-Validierungs-Tests (Tag 5)
uv run pytest test_validation.py -v

# Alle Tests auf einmal
uv run pytest -v
```

---

## 📁 Projektstruktur

```
my-first-api/
├── main.py                        # FastAPI Backend (Tag 1–5)
├── frontend.py                    # Streamlit Frontend (Tag 7)
├── test_validation.py             # Pydantic-Validierungs-Tests (Tag 5)
├── work-log.md                    # Lerntagebuch (Tag 1–9)
├── CLAUDE.md                      # Architektur-Dokumentation
├── pyproject.toml                 # Projektabhängigkeiten
├── uv.lock                        # Lockfile
├── data/
│   └── notes.json                 # Legacy JSON-Persistenz (Tag 2, historisch)
└── Exploration/
    └── class_based_decorator.py   # Decorator-Exploration (Tag 6)
```

---

## 🏛️ API-Übersicht

### Tag 1 — Basis-Endpunkte

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| `GET` | `/` | Hello World & API-Info |
| `GET` | `/status` | API-Status und Version |
| `GET` | `/about` | Projektmetadaten |
| `GET` | `/square/{number}` | Quadratzahl berechnen |
| `GET` | `/student` | Studierenden-Info |
| `GET` | `/double/{number}` | Zahl verdoppeln |

### Tag 2–5 — Notes CRUD

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| `POST` | `/notes` | Neue Notiz erstellen (201) |
| `GET` | `/notes` | Alle Notizen (mit Filtern) |
| `GET` | `/notes/stats` | Statistiken (total, by_category, top_tags) |
| `GET` | `/notes/{id}` | Einzelne Notiz abrufen |
| `PUT` | `/notes/{id}` | Notiz vollständig ersetzen |
| `PATCH` | `/notes/{id}` | Notiz partiell aktualisieren |
| `DELETE` | `/notes/{id}` | Notiz löschen (204) |

### Tag 3 — Kategorien & Tags als Ressourcen

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| `GET` | `/categories` | Alle genutzten Kategorien |
| `GET` | `/categories/{name}/notes` | Notizen einer Kategorie |
| `GET` | `/tags` | Alle genutzten Tags |
| `GET` | `/tags/{name}/notes` | Notizen mit einem Tag |

### Query-Parameter für `GET /notes`

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `category` | string | Exakte Kategorie-Filterung |
| `search` | string | Suche in Titel und Inhalt |
| `tag` | string | Exakte Tag-Filterung |
| `created_after` | ISO 8601 | Nur Notizen nach diesem Datum |
| `created_before` | ISO 8601 | Nur Notizen vor diesem Datum |

---

## 🗄️ Datenbankdesign

Die App nutzt **SQLite** über **SQLModel** (Pydantic + SQLAlchemy).

Tags werden über eine echte **Many-to-Many-Beziehung** (`NoteTagLink`) mit Notizen verknüpft — nicht als CSV-String. Jeder Tag existiert genau einmal in der `tags`-Tabelle und wird über die Verknüpfungstabelle mit beliebig vielen Notizen verbunden.

```
notes ──── NoteTagLink ──── tags
  id            note_id       id
  title         tag_id        name (unique)
  content
  category
  created_at
```

**Kritische Route-Reihenfolge:** `/notes/stats` muss **vor** `/notes/{note_id}` definiert sein, da FastAPI top-down matched und `stats` sonst als Integer-ID interpretiert wird (→ 422).

---

## ✅ Pydantic-Validierung (Tag 5)

`NoteCreate` und `NoteUpdate` erzwingen:

| Feld | Regel |
|------|-------|
| `title` | 3–100 Zeichen |
| `content` | 1–10.000 Zeichen |
| `category` | Muss in `{work, personal, school, ideas, general}` sein |
| `tags` | Max. 10 Tags, jeder mind. 2 Zeichen, automatisch normalisiert |
| *(global)* | `extra="forbid"`: unbekannte Felder → 422 |
| *(global)* | `str_strip_whitespace=True`: Whitespace wird automatisch entfernt |

Tags werden automatisch **lowercased**, **gestrippt** und **dedupliziert**.

---

## 📚 Technologie-Stack

| Technologie | Version | Verwendung |
|-------------|---------|-----------|
| Python | 3.14 | Laufzeitumgebung |
| FastAPI | ≥ 0.136 | Web-Framework |
| SQLModel | ≥ 0.0.38 | ORM + Pydantic-Integration |
| Pydantic | ≥ 2.13 | Datenvalidierung |
| Streamlit | ≥ 1.57 | Frontend |
| pytest | ≥ 9.0 | Testing |
| uv | — | Paketmanagement |
