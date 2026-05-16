"""
Notizen REST API — Emre Kartalel — Angewandte Programmierung
============================================================

Funktionen (Tag 1 – Tag 5):
  • Tag 1 : Basis-Endpunkte (/, /status, /about, /square, /student, /double)
  • Tag 2 : Notizen CRUD mit JSON-Speicherung
  • Tag 3 : Migration auf echte SQLite-Datenbank (SQLModel), Filter, Tags
  • Tag 5 : Strikte Pydantic Validierung (Längenbeschränkungen, Kategorien)

Starten:
    uv run fastapi dev main.py
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
# Verbindungstabelle (Many-to-Many: Notiz ↔ Tag)
# ===========================================================================

class NoteTagLink(SQLModel, table=True):
    """Verknüpft Notizen und Tags miteinander."""
    note_id: Optional[int] = SQLField(
        default=None, foreign_key="notes.id", primary_key=True
    )
    tag_id: Optional[int] = SQLField(
        default=None, foreign_key="tags.id", primary_key=True
    )

# ===========================================================================
# SQLModel Datenbankmodelle (Das, was in der DB landet)
# ===========================================================================

class Note(SQLModel, table=True):
    """Die eigentliche Notiz in der Datenbank."""
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
    """Ein einzelner Tag (z.B. 'wichtig', 'klausur')."""
    __tablename__ = "tags"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    name: str = SQLField(unique=True, index=True)

    notes: list[Note] = Relationship(
        back_populates="tags", link_model=NoteTagLink
    )

# ===========================================================================
# Pydantic API-Modelle (Ein- und Ausgabe der API)
# ===========================================================================

# Passend zu deinen Tests aus Tag 2 auf Deutsch!
ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {"arbeit", "privat", "uni", "ideen", "allgemein"}
)

class NoteCreate(BaseModel):
    """Daten, die der Nutzer beim Erstellen einer Notiz schickt."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    content: str = Field(min_length=1, max_length=10_000)
    category: str = Field(min_length=2, max_length=30)
    tags: list[str] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Prüft, ob die Kategorie erlaubt ist und macht sie klein."""
        normalised = v.lower().strip()
        if normalised not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Kategorie ungültig. Erlaubt sind: {', '.join(sorted(ALLOWED_CATEGORIES))}"
            )
        return normalised

    @field_validator("tags")
    @classmethod
    def validate_and_normalise_tags(cls, v: list[str]) -> list[str]:
        """Bereinigt die Tags (Kleinbuchstaben, keine Duplikate)."""
        if len(v) > 10:
            raise ValueError("Eine Notiz darf maximal 10 Tags haben.")
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            stripped = raw.strip()
            if len(stripped) < 2:
                raise ValueError(f"Der Tag '{raw}' ist zu kurz (min. 2 Zeichen).")
            normalised = stripped.lower()
            if normalised not in seen:
                seen.add(normalised)
                result.append(normalised)
        return result

class NoteUpdate(BaseModel):
    """Daten für ein partielles Update (PATCH). Alle Felder sind optional."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    content: Optional[str] = Field(default=None, min_length=1, max_length=10_000)
    category: Optional[str] = Field(default=None, min_length=2, max_length=30)
    tags: Optional[list[str]] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalised = v.lower().strip()
        if normalised not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Kategorie ungültig. Erlaubt sind: {', '.join(sorted(ALLOWED_CATEGORIES))}"
            )
        return normalised

    @field_validator("tags")
    @classmethod
    def validate_and_normalise_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Eine Notiz darf maximal 10 Tags haben.")
        seen: set[str] = set()
        result: list[str] = []
        for raw in v:
            stripped = raw.strip()
            if len(stripped) < 2:
                raise ValueError(f"Der Tag '{raw}' ist zu kurz.")
            normalised = stripped.lower()
            if normalised not in seen:
                seen.add(normalised)
                result.append(normalised)
        return result

class NoteResponse(BaseModel):
    """So sieht die Notiz aus, wenn die API sie zurückgibt."""
    id: int
    title: str
    content: str
    category: str
    tags: list[str]
    created_at: str

    model_config = ConfigDict(from_attributes=True)

class TagStats(BaseModel):
    """Statistik für einen einzelnen Tag."""
    tag: str
    count: int

class StatsResponse(BaseModel):
    """Das Ergebnis des Statistik-Endpunkts."""
    total_notes: int
    by_category: dict[str, int]
    top_tags: list[TagStats]
    unique_tags_count: int

# ===========================================================================
# API Setup & Lebenszyklus
# ===========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Wird beim Starten des Servers ausgeführt (erstellt die DB)."""
    create_db_and_tables()
    yield

app = FastAPI(
    title="Emres Notizen API",
    description="Ein Projekt für den Kurs Angewandte Programmierung an der Hochschule Coburg.",
    version="3.0.0",
    lifespan=lifespan,
)

# ===========================================================================
# Datenbank-Session (Dependency)
# ===========================================================================

def get_session() -> Session:
    """Stellt für jeden API-Aufruf eine frische Datenbankverbindung bereit."""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ===========================================================================
# Hilfsfunktionen
# ===========================================================================

def _get_or_create_tags(tag_names: list[str], session: Session) -> list[Tag]:
    """Sucht nach existierenden Tags oder erstellt neue, falls nötig."""
    tag_objects: list[Tag] = []
    for name in tag_names:
        statement = select(Tag).where(Tag.name == name)
        existing = session.exec(statement).first()
        if existing:
            tag_objects.append(existing)
        else:
            new_tag = Tag(name=name)
            session.add(new_tag)
            tag_objects.append(new_tag)
    return tag_objects

def _note_to_response(note: Note) -> NoteResponse:
    """Wandelt das Datenbank-Objekt in ein sauberes Pydantic-Objekt um."""
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=sorted(tag.name for tag in note.tags),
        created_at=note.created_at.isoformat(),
    )

def _get_note_or_404(note_id: int, session: Session) -> Note:
    """Sucht eine Notiz oder wirft einen 404 Fehler."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(
            status_code=404, detail=f"Notiz mit ID {note_id} wurde nicht gefunden."
        )
    return note

def _make_tz_aware(dt: datetime) -> datetime:
    """Stellt sicher, dass das Datum eine Zeitzone hat."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# ===========================================================================
# Tag 1: Basis-Endpunkte
# ===========================================================================

@app.get("/")
def read_root() -> dict:
    return {
        "message": "Hallo Welt!",
        "api": "Emres Notizen API",
        "version": "3.0.0",
    }

@app.get("/status")
def get_status() -> dict:
    return {"status": "online", "version": "3.0.0", "day": 3}

@app.get("/about")
def get_about() -> dict:
    return {
        "project": "Notizen API",
        "author": "Emre Kartalel",
        "course": "Angewandte Programmierung",
        "university": "Hochschule Coburg",
    }

@app.get("/square/{number}")
def calculate_square(number: int) -> dict:
    result = number * number
    return {"number": number, "square": result, "calculation": f"{number} × {number} = {result}"}

@app.get("/student")
def get_student() -> dict:
    return {
        "name": "Emre Kartalel",
        "semester": 2,
        "course": "Wirtschaftsinformatik 2.0",
        "university": "Hochschule Coburg",
    }

@app.get("/double/{number}")
def calculate_double(number: int) -> dict:
    result = number * 2
    return {"number": number, "double": result, "calculation": f"{number} × 2 = {result}"}

# ===========================================================================
# Notizen Endpunkte (CRUD)
# ===========================================================================

@app.post("/notes", status_code=201)
def create_note(note: NoteCreate, session: SessionDep) -> NoteResponse:
    """Erstellt eine neue Notiz und verknüpft die Tags."""
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
    """Gibt eine Statistik über alle Notizen zurück."""
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
    """Gibt alle Notizen zurück (mit optionalen Filtern für Suche, Datum etc.)."""
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
    """Holt eine spezifische Notiz anhand der ID."""
    return _note_to_response(_get_note_or_404(note_id, session))

@app.put("/notes/{note_id}")
def update_note(
    note_id: int, note_update: NoteCreate, session: SessionDep
) -> NoteResponse:
    """Ersetzt eine komplette Notiz (PUT)."""
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
    """Aktualisiert nur bestimmte Felder einer Notiz (PATCH)."""
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
    """Löscht eine Notiz."""
    note = _get_note_or_404(note_id, session)
    session.delete(note)
    session.commit()

# ===========================================================================
# Tags & Kategorien Endpunkte
# ===========================================================================

@app.get("/tags")
def list_tags(session: SessionDep) -> list[str]:
    """Gibt eine Liste aller existierenden Tags zurück."""
    tags = session.exec(select(Tag)).all()
    return sorted(tag.name for tag in tags)

@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str, session: SessionDep) -> list[NoteResponse]:
    """Sucht alle Notizen, die einen bestimmten Tag haben."""
    tag_lower = tag_name.lower().strip()
    tag = session.exec(select(Tag).where(Tag.name == tag_lower)).first()
    if not tag:
        return []
    return [_note_to_response(note) for note in tag.notes]

@app.get("/categories")
def list_categories(session: SessionDep) -> list[str]:
    """Gibt alle genutzten Kategorien zurück."""
    notes = session.exec(select(Note)).all()
    return sorted({note.category for note in notes})

@app.get("/categories/{category_name}/notes")
def get_notes_by_category(
    category_name: str, session: SessionDep
) -> list[NoteResponse]:
    """Sucht alle Notizen einer bestimmten Kategorie."""
    notes = session.exec(
        select(Note).where(Note.category == category_name)
    ).all()
    return [_note_to_response(note) for note in notes]