"""
Notizen REST API — Emre Kartalel — Angewandte Programmierung
============================================================

Funktionen (Tag 1 – Tag 5):
  • Tag 1 : Basis-Endpunkte (/, /status, /about, /square, /student, /double)
  • Tag 2 : Notizen CRUD mit JSON-Dateipersistenz (historisch)
  • Tag 3 : Migration auf SQLite via SQLModel, vollständiges REST-CRUD,
            Query-Filter, Tags- und Kategorien-Ressourcen, Datum-Filter
  • Tag 5 : Strikte Pydantic-Validierung (Field-Constraints, field_validator,
            ConfigDict)

Starten:
    uv run fastapi dev main.py

Testen (Server muss laufen):
    uv run pytest test_main.py -v
    uv run pytest test_validation.py -v
"""

from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlmodel import (
    Field as SQLField,
    Relationship,
    Session,
    SQLModel,
    col,
    create_engine,
    or_,
    select,
)

# ===========================================================================
# Datenbank-Setup
# ===========================================================================

DATABASE_URL = "sqlite:///notes.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Erstellt alle Tabellen in der SQLite-Datenbank beim Start."""
    SQLModel.metadata.create_all(engine)


# ===========================================================================
# Verbindungstabelle (Many-to-Many: Note ↔ Tag)
# ===========================================================================


class NoteTagLink(SQLModel, table=True):
    """Verknüpfungstabelle zwischen Notizen und Tags (M:N-Beziehung)."""

    note_id: Optional[int] = SQLField(
        default=None, foreign_key="notes.id", primary_key=True
    )
    tag_id: Optional[int] = SQLField(
        default=None, foreign_key="tags.id", primary_key=True
    )


# ===========================================================================
# SQLModel Datenbankmodelle
# ===========================================================================


class Note(SQLModel, table=True):
    """Persistierte Notiz in der SQLite-Datenbank."""

    __tablename__ = "notes"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str = SQLField(index=True)
    content: str
    category: str = SQLField(index=True)
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    tags: list["Tag"] = Relationship(
        back_populates="notes", link_model=NoteTagLink
    )


class Tag(SQLModel, table=True):
    """Eindeutiger, normalisierter Tag (immer Kleinbuchstaben)."""

    __tablename__ = "tags"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(unique=True, index=True)

    notes: list[Note] = Relationship(
        back_populates="tags", link_model=NoteTagLink
    )


# ===========================================================================
# Pydantic API-Modelle — Eingabe und Ausgabe
# ===========================================================================

# Vom Dozenten vorgegebene Kategorien (Day 5, Task 2)
ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"work", "personal", "school", "ideas", "general"}
)


class NoteCreate(BaseModel):
    """Request-Body für POST /notes und PUT /notes/{id}.

    Validierungsregeln (Day 5):
      - title    : 3–100 Zeichen, Pflichtfeld
      - content  : 1–10.000 Zeichen, Pflichtfeld
      - category : muss in ALLOWED_CATEGORIES sein, wird normalisiert
      - tags     : max. 10 Einträge, jeder mind. 2 Zeichen, normalisiert
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=1, max_length=10_000)
    category: str = Field(min_length=2, max_length=30)
    tags: list[str] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Normalisiert die Kategorie und prüft gegen die Whitelist."""
        normalised = v.lower().strip()
        if normalised not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Category must be one of: "
                f"{', '.join(sorted(ALLOWED_CATEGORIES))}"
            )
        return normalised

    @field_validator("tags")
    @classmethod
    def validate_and_normalise_tags(cls, v: list[str]) -> list[str]:
        """Begrenzt, bereinigt, lowercased und dedupliziert die Tags."""
        if len(v) > 10:
            raise ValueError("A note can have at most 10 tags.")
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            stripped = raw.strip()
            if len(stripped) < 2:
                raise ValueError(
                    f"Tag '{raw}' must be at least 2 characters after stripping."
                )
            normalised = stripped.lower()
            if normalised not in seen:
                seen.add(normalised)
                result.append(normalised)
        return result


class NoteUpdate(BaseModel):
    """Request-Body für PATCH /notes/{id}.

    Alle Felder sind optional — nur angegebene Felder werden aktualisiert.
    Die Validierungsregeln von NoteCreate gelten, wenn ein Feld vorhanden ist.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10_000)
    category: Optional[str] = Field(default=None, min_length=2, max_length=30)
    tags: Optional[list[str]] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Normalisiert und validiert die Kategorie wenn angegeben."""
        if v is None:
            return v
        normalised = v.lower().strip()
        if normalised not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Category must be one of: "
                f"{', '.join(sorted(ALLOWED_CATEGORIES))}"
            )
        return normalised

    @field_validator("tags")
    @classmethod
    def validate_and_normalise_tags(
        cls, v: Optional[list[str]]
    ) -> Optional[list[str]]:
        """Validiert und normalisiert Tags wenn angegeben."""
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("A note can have at most 10 tags.")
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            stripped = raw.strip()
            if len(stripped) < 2:
                raise ValueError(
                    f"Tag '{raw}' must be at least 2 characters after stripping."
                )
            normalised = stripped.lower()
            if normalised not in seen:
                seen.add(normalised)
                result.append(normalised)
        return result


class NoteResponse(BaseModel):
    """API-Antwortformat für eine einzelne Notiz."""

    id: int
    title: str
    content: str
    category: str
    tags: list[str]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TagStats(BaseModel):
    """Einzelner Eintrag in der Top-Tags-Liste der Statistik."""

    tag: str
    count: int


class StatsResponse(BaseModel):
    """Aggregierte Statistiken aller Notizen."""

    total_notes: int
    by_category: dict[str, int]
    top_tags: list[TagStats]
    unique_tags_count: int


# ===========================================================================
# FastAPI App und Lebenszyklus
# ===========================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Erstellt die Datenbanktabellen beim Start des Servers."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Emres Notizen API",
    description=(
        "Eine produktionsreife REST API mit FastAPI und SQLite.\n\n"
        "**Kurs:** Angewandte Programmierung — Hochschule Coburg\n"
        "**Autor:** Emre Kartalel"
    ),
    version="3.0.0",
    lifespan=lifespan,
)


# ===========================================================================
# Datenbank-Session Dependency
# ===========================================================================


def get_session() -> Session:
    """Stellt für jeden Request eine frische Datenbankverbindung bereit."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# ===========================================================================
# Hilfsfunktionen
# ===========================================================================


def _get_or_create_tags(tag_names: list[str], session: Session) -> list[Tag]:
    """Gibt Tag-Objekte zurück und erstellt neue, falls noch nicht vorhanden."""
    tag_objects: list[Tag] = []
    for name in tag_names:
        existing = session.exec(select(Tag).where(Tag.name == name)).first()
        if existing:
            tag_objects.append(existing)
        else:
            new_tag = Tag(name=name)
            session.add(new_tag)
            tag_objects.append(new_tag)
    return tag_objects


def _note_to_response(note: Note) -> NoteResponse:
    """Konvertiert ein SQLModel-Objekt in das Pydantic-Antwortformat."""
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=sorted(tag.name for tag in note.tags),
        created_at=note.created_at.isoformat(),
    )


def _get_note_or_404(note_id: int, session: Session) -> Note:
    """Gibt eine Notiz zurück oder wirft HTTP 404."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with ID {note_id} not found.",
        )
    return note


def _make_tz_aware(dt: datetime) -> datetime:
    """Macht ein datetime-Objekt timezone-aware (UTC als Fallback)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ===========================================================================
# Tag 1: Basis-Endpunkte
# ===========================================================================


@app.get("/")
def read_root() -> dict:
    """Gibt grundlegende API-Metadaten zurück."""
    return {
        "message": "Hello World!",
        "api": "Emres Notizen API",
        "version": "3.0.0",
    }


@app.get("/status")
def get_status() -> dict:
    """Gibt den aktuellen API-Status zurück."""
    return {"status": "online", "version": "3.0.0", "day": 3}


@app.get("/about")
def get_about() -> dict:
    """Gibt Projektmetadaten zurück."""
    return {
        "project": "Notizen API",
        "author": "Emre Kartalel",
        "course": "Angewandte Programmierung",
        "university": "Hochschule Coburg",
    }


@app.get("/square/{number}")
def calculate_square(number: int) -> dict:
    """Berechnet das Quadrat einer ganzen Zahl."""
    result = number * number
    return {
        "number": number,
        "square": result,
        "calculation": f"{number} × {number} = {result}",
    }


@app.get("/student")
def get_student() -> dict:
    """Gibt persönliche Studierenden-Informationen zurück."""
    return {
        "name": "Emre Kartalel",
        "semester": 2,
        "course": "Wirtschaftsinformatik 2.0",
        "university": "Hochschule Coburg",
    }


@app.get("/double/{number}")
def calculate_double(number: int) -> dict:
    """Verdoppelt eine ganze Zahl."""
    result = number * 2
    return {
        "number": number,
        "double": result,
        "calculation": f"{number} × 2 = {result}",
    }


# ===========================================================================
# Notizen-Endpunkte
# ⚠️  WICHTIG: Statische Pfade (/notes/stats) MÜSSEN vor dynamischen
#     Pfaden (/notes/{note_id}) definiert sein — FastAPI matched top-down.
# ===========================================================================


@app.post("/notes", status_code=201)
def create_note(note: NoteCreate, session: SessionDep) -> NoteResponse:
    """Erstellt eine neue Notiz.

    Tags werden normalisiert (Kleinbuchstaben, dedupliziert) und über eine
    Many-to-Many-Beziehung mit der Notiz verknüpft.
    """
    tag_objects = _get_or_create_tags(note.tags, session)
    db_note = Note(
        title=note.title,
        content=note.content,
        category=note.category,
        tags=tag_objects,
    )
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    return _note_to_response(db_note)


@app.get("/notes/stats")
def get_note_stats(session: SessionDep) -> StatsResponse:
    """Gibt aggregierte Statistiken über alle Notizen zurück.

    Enthält: Gesamtanzahl, Aufschlüsselung nach Kategorie,
    Top-5-Tags (absteigend nach Häufigkeit) und Anzahl eindeutiger Tags.

    Muss VOR /notes/{note_id} definiert sein (Routing-Konflikt vermeiden).
    """
    notes = session.exec(select(Note)).all()

    by_category: dict[str, int] = {}
    tag_counter: Counter = Counter()

    for note in notes:
        by_category[note.category] = by_category.get(note.category, 0) + 1
        for tag in note.tags:
            tag_counter[tag.name] += 1

    top_tags = [
        TagStats(tag=name, count=count)
        for name, count in tag_counter.most_common(5)
    ]

    # Eindeutige Tags aus der Tag-Tabelle — konsistent mit GET /tags
    all_db_tags = session.exec(select(Tag)).all()

    return StatsResponse(
        total_notes=len(notes),
        by_category=by_category,
        top_tags=top_tags,
        unique_tags_count=len(all_db_tags),
    )


@app.get("/notes")
def list_notes(
    session: SessionDep,
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> list[NoteResponse]:
    """Gibt alle Notizen zurück — alle Filter sind kombinierbar.

    - **category**: exakte Übereinstimmung mit der Kategorie
    - **search**: Teilstring-Suche in Titel und Inhalt (case-insensitive)
    - **tag**: exakte Tag-Suche (case-insensitive, normalisiert)
    - **created_after**: ISO 8601 Datum, z.B. `2026-04-01`
    - **created_before**: ISO 8601 Datum, z.B. `2026-04-30`
    """
    statement = select(Note)

    if category is not None:
        statement = statement.where(Note.category == category)

    if search is not None:
        statement = statement.where(
            or_(
                col(Note.title).ilike(f"%{search}%"),
                col(Note.content).ilike(f"%{search}%"),
            )
        )

    if tag is not None:
        tag_lower = tag.lower().strip()
        statement = statement.join(Note.tags).where(Tag.name == tag_lower)

    notes = session.exec(statement).all()

    if created_after is not None:
        ca = _make_tz_aware(created_after)
        notes = [n for n in notes if n.created_at >= ca]

    if created_before is not None:
        cb = _make_tz_aware(created_before)
        notes = [n for n in notes if n.created_at <= cb]

    return [_note_to_response(n) for n in notes]


@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep) -> NoteResponse:
    """Gibt eine einzelne Notiz anhand ihrer ID zurück."""
    return _note_to_response(_get_note_or_404(note_id, session))


@app.put("/notes/{note_id}")
def update_note(
    note_id: int, note_update: NoteCreate, session: SessionDep
) -> NoteResponse:
    """Ersetzt eine Notiz vollständig (PUT).

    ID und Erstellungszeitpunkt bleiben erhalten.
    Alle Felder aus NoteCreate sind Pflichtfelder.
    """
    note = _get_note_or_404(note_id, session)
    note.title = note_update.title
    note.content = note_update.content
    note.category = note_update.category
    note.tags = _get_or_create_tags(note_update.tags, session)
    session.add(note)
    session.commit()
    session.refresh(note)
    return _note_to_response(note)


@app.patch("/notes/{note_id}")
def partial_update_note(
    note_id: int, note_update: NoteUpdate, session: SessionDep
) -> NoteResponse:
    """Aktualisiert eine Notiz partiell (PATCH).

    Nur angegebene Felder werden geändert. Ein leerer Body `{}` ist
    gültig und ändert nichts.
    """
    note = _get_note_or_404(note_id, session)

    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    if note_update.category is not None:
        note.category = note_update.category
    if note_update.tags is not None:
        note.tags = _get_or_create_tags(note_update.tags, session)

    session.add(note)
    session.commit()
    session.refresh(note)
    return _note_to_response(note)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, session: SessionDep) -> None:
    """Löscht eine Notiz anhand ihrer ID.

    Gibt 204 No Content bei Erfolg zurück, 404 wenn nicht gefunden.
    """
    note = _get_note_or_404(note_id, session)
    session.delete(note)
    session.commit()


# ===========================================================================
# Tags-Ressourcen
# ===========================================================================


@app.get("/tags")
def list_tags(session: SessionDep) -> list[str]:
    """Gibt alle eindeutigen Tags in alphabetischer Reihenfolge zurück."""
    tags = session.exec(select(Tag)).all()
    return sorted(tag.name for tag in tags)


@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str, session: SessionDep) -> list[NoteResponse]:
    """Gibt alle Notizen mit einem bestimmten Tag zurück (case-insensitive).

    Gibt eine leere Liste zurück wenn der Tag nicht existiert — kein 404.
    """
    tag_lower = tag_name.lower().strip()
    tag = session.exec(select(Tag).where(Tag.name == tag_lower)).first()
    if not tag:
        return []
    return [_note_to_response(note) for note in tag.notes]


# ===========================================================================
# Kategorien-Ressourcen
# ===========================================================================


@app.get("/categories")
def list_categories(session: SessionDep) -> list[str]:
    """Gibt alle genutzten Kategorien in alphabetischer Reihenfolge zurück."""
    notes = session.exec(select(Note)).all()
    return sorted({note.category for note in notes})


@app.get("/categories/{category_name}/notes")
def get_notes_by_category(
    category_name: str, session: SessionDep
) -> list[NoteResponse]:
    """Gibt alle Notizen einer bestimmten Kategorie zurück.

    Gibt eine leere Liste zurück wenn keine Notizen gefunden — kein 404.
    """
    notes = session.exec(
        select(Note).where(Note.category == category_name)
    ).all()
    return [_note_to_response(note) for note in notes]
