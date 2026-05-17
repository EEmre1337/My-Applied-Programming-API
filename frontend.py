"""
Streamlit Frontend — Emre Kartalel — Angewandte Programmierung Tag 7
====================================================================

Startet mit:
    uv run streamlit run frontend.py

Das FastAPI-Backend muss parallel laufen:
    uv run fastapi dev main.py
"""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

# Kategorien: API-Wert → Anzeigetext
CATEGORY_LABELS: dict[str, str] = {
    "work": "Arbeit",
    "personal": "Privat",
    "school": "Schule / Uni",
    "ideas": "Ideen",
    "general": "Allgemein",
}

st.set_page_config(page_title="Notizen App", page_icon="📝", layout="wide")
st.title("📝 Meine Notizen App")
st.markdown("Ein Streamlit-Frontend für die FastAPI Notes-API.")

# ---------------------------------------------------------------------------
# Hilfsfunktion: API erreichbar?
# ---------------------------------------------------------------------------


def _api_is_online() -> bool:
    try:
        requests.get(f"{API_URL}/", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False


if not _api_is_online():
    st.error(
        "⚠️ API nicht erreichbar — bitte Backend starten: "
        "`uv run fastapi dev main.py`"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Layout: zwei Spalten
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([1, 2])

# ===========================================================================
# Linke Spalte: Neue Notiz anlegen
# ===========================================================================

with col_left:
    st.subheader("➕ Neue Notiz anlegen")

    with st.form("new_note_form", clear_on_submit=True):
        title = st.text_input("Titel", placeholder="Mind. 3 Zeichen …")
        content = st.text_area("Inhalt", placeholder="Worum geht es?")
        category = st.selectbox(
            "Kategorie",
            options=list(CATEGORY_LABELS.keys()),
            format_func=lambda k: CATEGORY_LABELS[k],
        )
        tags_input = st.text_input(
            "Tags (kommagetrennt)",
            placeholder="z.B. wichtig, deadline",
        )
        submitted = st.form_submit_button("💾 Notiz speichern")

    if submitted:
        # Komma-getrennte Tags in Liste umwandeln, leere Einträge filtern
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]

        payload = {
            "title": title,
            "content": content,
            "category": category,
            "tags": tags,
        }

        try:
            res = requests.post(f"{API_URL}/notes", json=payload)
            if res.status_code == 201:
                st.success("✅ Notiz erfolgreich erstellt!")
                st.rerun()
            else:
                # Pydantic-Fehler lesbar anzeigen
                detail = res.json().get("detail", res.text)
                st.error(f"❌ Fehler ({res.status_code}): {detail}")
        except requests.exceptions.ConnectionError:
            st.error("Verbindungsfehler — läuft das Backend?")

# ===========================================================================
# Rechte Spalte: Alle Notizen anzeigen
# ===========================================================================

with col_right:
    st.subheader("📋 Alle Notizen")

    # Filterleiste
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_category = st.selectbox(
            "Nach Kategorie filtern",
            options=["Alle"] + list(CATEGORY_LABELS.keys()),
            format_func=lambda k: "Alle Kategorien" if k == "Alle" else CATEGORY_LABELS[k],
        )
    with filter_col2:
        filter_search = st.text_input("Suche (Titel / Inhalt)", placeholder="Suchbegriff …")
    with filter_col3:
        filter_tag = st.text_input("Nach Tag filtern", placeholder="z.B. urgent")

    # API-Anfrage mit Filtern
    params: dict = {}
    if filter_category != "Alle":
        params["category"] = filter_category
    if filter_search:
        params["search"] = filter_search
    if filter_tag:
        params["tag"] = filter_tag.strip().lower()

    try:
        res = requests.get(f"{API_URL}/notes", params=params)
        notes = res.json() if res.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        notes = []

    if not notes:
        st.info("Keine Notizen gefunden.")
    else:
        st.caption(f"{len(notes)} Notiz(en) gefunden.")
        for note in notes:
            category_label = CATEGORY_LABELS.get(note["category"], note["category"])
            header = f"📌 **{note['title']}** — {category_label}"
            with st.expander(header):
                st.write(note["content"])
                if note.get("tags"):
                    st.caption("🏷️ Tags: " + ", ".join(note["tags"]))
                st.caption(f"🕒 Erstellt: {note['created_at'][:19].replace('T', ' ')} UTC")

                # Notiz löschen
                if st.button("🗑️ Löschen", key=f"delete_{note['id']}"):
                    del_res = requests.delete(f"{API_URL}/notes/{note['id']}")
                    if del_res.status_code == 204:
                        st.success("Notiz gelöscht.")
                        st.rerun()
                    else:
                        st.error("Fehler beim Löschen.")
