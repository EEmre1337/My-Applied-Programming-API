import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Notes App", page_icon="📝")
st.title("📝 Meine Notizen App")
st.markdown("Ein Streamlit-Frontend für unsere FastAPI Notes-API.")

# -------------------------------------------------------------------
# Formular: Neue Notiz anlegen
# -------------------------------------------------------------------
with st.form("new_note_form"):
    st.subheader("Neue Notiz anlegen")
    title = st.text_input("Titel (min. 3 Zeichen)")
    content = st.text_area("Inhalt")
    category = st.selectbox("Kategorie", ["arbeit", "privat", "uni", "ideen", "allgemein"])
    tags_input = st.text_input("Tags (kommagetrennt, z.B. wichtig, klausur)")
    
    submit = st.form_submit_button("Notiz Speichern")

    if submit:
        # String zu Liste konvertieren und leere Tags filtern
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        
        payload = {
            "title": title,
            "content": content,
            "category": category,
            "tags": tags
        }
        
        try:
            res = requests.post(f"{API_URL}/notes", json=payload)
            if res.status_code == 201:
                st.success("Notiz erfolgreich erstellt!")
            else:
                st.error(f"Validierungsfehler: {res.text}")
        except requests.exceptions.ConnectionError:
            st.error("Verbindungsfehler: Läuft das FastAPI Backend (uv run fastapi dev main.py)?")

st.divider()

# -------------------------------------------------------------------
# Liste: Alle Notizen anzeigen
# -------------------------------------------------------------------
st.subheader("Alle Notizen")

try:
    res = requests.get(f"{API_URL}/notes")
    if res.status_code == 200:
        notes = res.json()
        if not notes:
            st.info("Noch keine Notizen vorhanden.")
        else:
            for note in notes:
                # Expander für Detailansicht (wie im Work Log beschrieben)
                with st.expander(f"📌 {note['title']} ({note['category']})"):
                    st.write(note["content"])
                    if note.get("tags"):
                        st.caption(f"Tags: {', '.join(note['tags'])}")
                    st.caption(f"Erstellt am: {note['created_at']}")
    else:
        st.error(f"Fehler beim Laden: {res.status_code}")
except requests.exceptions.ConnectionError:
    st.warning("Verbindungsfehler: API nicht erreichbar.")