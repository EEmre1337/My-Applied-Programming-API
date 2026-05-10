from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import json
from pathlib import Path

app = FastAPI(title="Emres API - Day 1 & 2")

# --- TAG 1: Grundlagen ---

@app.get("/")
def read_root():
    return {"message": "Hello World!"}

@app.get("/status")
def get_status():
    return {"status": "online", "version": "0.1.0", "day": 1}

@app.get("/about")
def get_about():
    return {
        "project": "My First API",
        "author": "Emre Kartalel",
        "course": "Applied Programming"
    }

# --- Hausaufgaben Tag 1 ---

@app.get("/square/{number}")
def calculate_square(number: int):
    result = number * number
    return {"number": number, "square": result, "calculation": f"{number} × {number} = {result}"}

@app.get("/student")
def get_student():
    return {
        "name": "Emre Kartalel",
        "semester": 2,
        "course": "Wirtschaftsinformatik 2.0",
        "university": "Hochschule Coburg"
    }

@app.get("/double/{number}")
def calculate_double(number: int):
    result = number * 2
    return {"number": number, "double": result, "calculation": f"{number} × 2 = {result}"}


# ==========================================
# --- TAG 2: Note Taking API (Persistence) ---
# ==========================================

# 1. Models (Schritt 4)
class NoteCreate(BaseModel):
    title: str
    content: str
    category: str  # Hausaufgabe: Kategorie hinzufügen

class Note(BaseModel):
    id: int
    title: str
    content: str
    category: str
    created_at: str

# 2. Storage Setup (Schritt 5 & 12)
NOTES_FILE = Path("data/notes.json")

def load_notes():
    notes_db = []
    note_id_counter = 1
    if NOTES_FILE.exists():
        with open(NOTES_FILE, 'r') as f:
            data = json.load(f)
            notes_db = [Note(**note) for note in data]
            if notes_db:
                note_id_counter = max(note.id for note in notes_db) + 1
    return notes_db, note_id_counter

def save_notes(notes_db):
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTES_FILE, 'w') as f:
        notes_data = [note.model_dump() for note in notes_db]
        json.dump(notes_data, f, indent=2)

# 3. Endpunkte (Schritt 6 - 15)
@app.post("/notes", status_code=201)
def create_note(note: NoteCreate) -> Note:
    notes_db, note_id_counter = load_notes()
    new_note = Note(
        id=note_id_counter,
        title=note.title,
        content=note.content,
        category=note.category,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    notes_db.append(new_note)
    save_notes(notes_db)
    return new_note

@app.get("/notes")
def list_notes() -> list[Note]:
    notes_db, _ = load_notes()
    return notes_db

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    notes_db, _ = load_notes()
    for note in notes_db:
        if note.id == note_id:
            return note
    raise HTTPException(status_code=404, detail=f"Note {note_id} not found")

# --- Hausaufgabe Tag 2: Filter & Stats ---
@app.get("/notes/category/{category}")
def get_notes_by_category(category: str):
    notes_db, _ = load_notes()
    return [n for n in notes_db if n.category.lower() == category.lower()]

@app.get("/notes/stats")
def get_notes_stats():
    notes_db, _ = load_notes()
    categories = {}
    for note in notes_db:
        categories[note.category] = categories.get(note.category, 0) + 1
    return {
        "total_notes": len(notes_db),
        "by_category": categories
    }

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    """Löscht eine spezifische Notiz anhand ihrer ID."""
    notes_db, _ = load_notes()
    

    for i, note in enumerate(notes_db):
        if note.id == note_id:
            notes_db.pop(i)         
            save_notes(notes_db)    
            return {"message": f"Note {note_id} deleted successfully"}
    
    raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")