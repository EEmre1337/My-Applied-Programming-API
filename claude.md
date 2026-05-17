# CLAUDE.md — Projekt-Richtlinien & Architektur

Diese Datei beschreibt die Architektur, wichtige Befehle und Design-Entscheidungen der Notizen-API.

---

## 🚀 Wichtige Terminal-Befehle

| Aufgabe | Befehl |
|---------|--------|
| Abhängigkeiten installieren | `uv sync` |
| Paket hinzufügen | `uv add <paketname>` |
| Backend starten | `uv run fastapi dev main.py` |
| Frontend starten | `uv run streamlit run frontend.py` |
| Alle Tests ausführen | `uv run pytest -v` |
| Dozenten-Test-Suite | `uv run pytest test_main.py -v` |
| Validierungs-Tests | `uv run pytest test_validation.py -v` |

---

## 🏗️ Architektur-Überblick

```
Streamlit Frontend (frontend.py)
        │  HTTP requests
        ▼
FastAPI Backend (main.py)
        │  SQLModel ORM
        ▼
SQLite Datenbank (notes.db)
```

---

## 📁 Dateistruktur

```
my-first-api/
├── main.py                      # FastAPI App + SQLModel Modelle
├── frontend.py                  # Streamlit GUI
├── test_main.py                 # Offizielle Test-Suite des Dozenten
├── test_validation.py           # Pydantic-Validierungs-Tests (Tag 5)
├── work-log.md                  # Lerntagebuch
├── CLAUDE.md                    # Diese Datei
├── notes.db                     # SQLite-DB (auto-generiert, in .gitignore)
└── Exploration/
    └── class_based_decorator.py # Tag 6: Decorator-Exploration
```

---

## 🗄️ Datenbankschema

Drei Tabellen mit einer Many-to-Many-Beziehung zwischen `notes` und `tags`:

```
┌─────────────┐     ┌───────────────┐     ┌──────────┐
│    notes    │     │  notetaglink  │     │   tags   │
├─────────────┤     ├───────────────┤     ├──────────┤
│ id (PK)     │──┐  │ note_id (FK)  │  ┌──│ id (PK)  │
│ title       │  └─▶│ tag_id (FK)   │◀─┘  │ name     │
│ content     │     └───────────────┘     └──────────┘
│ category    │
│ created_at  │
└─────────────┘
```

---

## ⚠️ Kritische Design-Entscheidungen

### 1. Route-Reihenfolge
`/notes/stats` **muss vor** `/notes/{note_id}` definiert sein.
FastAPI matched Routen top-down. Steht `{note_id}` zuerst, interpretiert
FastAPI `"stats"` als Integer → 422 Validation Error.

### 2. Tag-Normalisierung
Tags werden beim Speichern automatisch:
- Whitespace gestrippt (`"  hello  "` → `"hello"`)
- Lowercased (`"URGENT"` → `"urgent"`)
- Dedupliziert (`["test", "Test"]` → `["test"]`)

### 3. Erlaubte Kategorien
```python
ALLOWED_CATEGORIES = {"work", "personal", "school", "ideas", "general"}
```
Jede andere Kategorie wird mit HTTP 422 abgelehnt.

### 4. Session nach commit() refreshen
Nach jedem `session.commit()` muss `session.refresh(obj)` aufgerufen
werden, um Lazy-Loading-Fehler (`DetachedInstanceError`) zu vermeiden.

### 5. Timezone-Handling
`created_at` wird immer mit UTC-Timezone gespeichert.
Query-Parameter ohne Timezone werden als UTC interpretiert.
