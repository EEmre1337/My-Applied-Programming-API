"""
Pytest Validierungs-Tests — Tag 5 Hausaufgabe.
==============================================

Testet, ob die NoteCreate und NoteUpdate Modelle ungültige Eingaben mit
einem HTTP 422 Fehler ablehnen und gültige Eingaben korrekt verarbeiten.

Starte zuerst die API in einem Terminal:
    uv run fastapi dev main.py

Und dann in einem ZWEITEN Terminal die Tests:
    uv run pytest test_validation.py -v
"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Session Fixture – Bricht alle Tests ab, falls die API gar nicht läuft
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _require_server():
    """Überspringt die gesamte Test-Suite, wenn die API offline ist."""
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"API ist unter {BASE_URL} nicht erreichbar: {exc}")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _valid_payload(**overrides) -> dict:
    """Gibt eine minimale, gültige Notiz zurück (mit optionalen Überschreibungen)."""
    base = {
        "title": "Valid Title",
        "content": "Some content here.",
        "category": "work",
        "tags": ["example", "test"],
    }
    base.update(overrides)
    return base


# ===========================================================================
# Aufgabe 1 – NoteCreate Feld-Beschränkungen (Constraints)
# ===========================================================================


def test_create_note_rejects_short_title():
    """Der Titel muss mindestens 3 Zeichen lang sein."""
    response = requests.post(f"{BASE_URL}/notes", json=_valid_payload(title="ab"))
    assert response.status_code == 422, response.text


def test_create_note_rejects_empty_title():
    """Ein komplett leerer Titel muss abgelehnt werden."""
    response = requests.post(f"{BASE_URL}/notes", json=_valid_payload(title=""))
    assert response.status_code == 422, response.text


def test_create_note_accepts_minimum_title():
    """Ein Titel mit genau 3 Zeichen sollte akzeptiert werden."""
    response = requests.post(f"{BASE_URL}/notes", json=_valid_payload(title="abc"))
    assert response.status_code == 201, response.text


def test_create_note_rejects_too_long_title():
    """Ein Titel mit über 100 Zeichen muss abgelehnt werden."""
    long_title = "a" * 101
    response = requests.post(f"{BASE_URL}/notes", json=_valid_payload(title=long_title))
    assert response.status_code == 422, response.text


def test_create_note_rejects_empty_content():
    """Der Inhalt einer Notiz darf nicht leer sein."""
    response = requests.post(f"{BASE_URL}/notes", json=_valid_payload(content=""))
    assert response.status_code == 422, response.text


def test_create_note_rejects_unknown_category():
    """Eine unbekannte Kategorie muss mit einem 422 Fehler scheitern."""
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(category="invalid-category")
    )
    assert response.status_code == 422, response.text


def test_create_note_accepts_all_allowed_categories():
    """Jede der erlaubten Kategorien muss von der API akzeptiert werden."""
    allowed = ["work", "personal", "school", "ideas", "general"]
    for cat in allowed:
        response = requests.post(
            f"{BASE_URL}/notes",
            json=_valid_payload(title=f"Test {cat}", category=cat),
        )
        assert response.status_code == 201, (
            f"Category '{cat}' was rejected: {response.text}"
        )


# ===========================================================================
# Aufgabe 2 – Tag Validierung
# ===========================================================================


def test_create_note_normalizes_tags():
    """Tags sollen automatisch klein geschrieben und Duplikate entfernt werden."""
    response = requests.post(
        f"{BASE_URL}/notes",
        json=_valid_payload(tags=["URGENT", "urgent", "Meeting"]),
    )
    assert response.status_code == 201, response.text
    assert sorted(response.json()["tags"]) == ["meeting", "urgent"]


def test_create_note_strips_tag_whitespace():
    """Leerzeichen um Tags herum müssen entfernt werden."""
    response = requests.post(
        f"{BASE_URL}/notes",
        json=_valid_payload(tags=["  hello  ", "hello"]),
    )
    assert response.status_code == 201, response.text
    assert response.json()["tags"] == ["hello"]


def test_create_note_rejects_single_char_tag():
    """Tags, die kürzer als 2 Zeichen sind, müssen mit 422 scheitern."""
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(tags=["a"])
    )
    assert response.status_code == 422, response.text


def test_create_note_accepts_two_char_tag():
    """Ein 2-Zeichen-Tag sollte akzeptiert werden."""
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(tags=["ab"])
    )
    assert response.status_code == 201, response.text
    assert "ab" in response.json()["tags"]


def test_create_note_rejects_more_than_10_tags():
    """Mehr als 10 Tags pro Notiz müssen abgelehnt werden (422)."""
    too_many = [f"tag{i:02d}" for i in range(11)]
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(tags=too_many)
    )
    assert response.status_code == 422, response.text


def test_create_note_accepts_exactly_10_tags():
    """Genau 10 Tags sollten gerade noch so akzeptiert werden."""
    ten_tags = [f"tag{i:02d}" for i in range(10)]
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(tags=ten_tags)
    )
    assert response.status_code == 201, response.text
    assert len(response.json()["tags"]) == 10


# ===========================================================================
# Aufgabe 3 – extra="forbid"
# ===========================================================================


def test_create_note_forbids_extra_fields():
    """Unbekannte Zusatzfelder im JSON müssen abgelehnt werden."""
    payload = _valid_payload()
    payload["unknown_field"] = "should not be allowed"
    response = requests.post(f"{BASE_URL}/notes", json=payload)
    assert response.status_code == 422, response.text


# ===========================================================================
# Aufgabe 4 – NoteUpdate (PATCH) Validierung
# ===========================================================================


def _create_test_note() -> dict:
    """Erstellt eine Notiz für die PATCH-Tests."""
    r = requests.post(
        f"{BASE_URL}/notes",
        json={
            "title": "Patch Me",
            "content": "Original content.",
            "category": "work",
        },
    )
    assert r.status_code == 201
    return r.json()


def test_patch_with_empty_body_succeeds():
    """Ein leerer PATCH-Request `{}` darf nichts ändern (Status 200)."""
    note = _create_test_note()
    response = requests.patch(f"{BASE_URL}/notes/{note['id']}", json={})
    assert response.status_code == 200, response.text
    assert response.json()["title"] == note["title"]


def test_patch_with_invalid_title_fails():
    """Ein PATCH mit einem zu kurzen Titel muss scheitern."""
    note = _create_test_note()
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"title": "ab"}
    )
    assert response.status_code == 422, response.text


def test_patch_with_invalid_category_fails():
    """Ein PATCH mit einer ungültigen Kategorie muss scheitern."""
    note = _create_test_note()
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"category": "invalid"}
    )
    assert response.status_code == 422, response.text


def test_patch_normalizes_category_to_lowercase():
    """Auch bei einem PATCH muss die Kategorie normalisiert werden."""
    note = _create_test_note()
    response = requests.patch(
        f"{BASE_URL}/notes/{note['id']}", json={"category": "PERSONAL"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["category"] == "personal"


# ===========================================================================
# Aufgabe 5 – Tag Normalisierung
# ===========================================================================


def test_tag_name_stored_as_lowercase():
    """Tags in Großbuchstaben müssen als Kleinbuchstaben gespeichert werden."""
    response = requests.post(
        f"{BASE_URL}/notes", json=_valid_payload(tags=["UPPERCASE"])
    )
    assert response.status_code == 201, response.text
    assert "uppercase" in response.json()["tags"]
    assert "UPPERCASE" not in response.json()["tags"]


def test_tag_reused_across_notes_appears_once_in_tags_list():
    """Ein Tag in mehreren Notizen darf in GET /tags nur einmal auftauchen."""
    unique_tag = "shared-unique-tag-xyz"
    requests.post(f"{BASE_URL}/notes", json=_valid_payload(tags=[unique_tag]))
    requests.post(f"{BASE_URL}/notes", json=_valid_payload(tags=[unique_tag]))

    tags = requests.get(f"{BASE_URL}/tags").json()
    assert tags.count(unique_tag) == 1
