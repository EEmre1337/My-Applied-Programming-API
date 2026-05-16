# Work Log
 
**Student Name:** Emre Kartalel
 
Instructions: Fill out one log for each course day. Content to consider: Course Sessions + Assignment
 
---
 
## Week 1
 
### Day 1
 
#### 1. ✅ What did I accomplish?
 
Ich habe an Tag 1 meine komplette Entwicklungsumgebung aufgesetzt: Git, VS Code mit Python-Extension und `uv` als Paketmanager installiert und jeweils mit `git --version` und `uv --version` verifiziert. Danach habe ich ein neues Projekt angelegt, FastAPI über `uv add fastapi[standard]` installiert und meine erste `main.py` geschrieben. Konkret habe ich drei Endpoints implementiert: `/` (Hello World), `/status` (API-Status mit Version) und `/about` (Projektinfo). Den Server habe ich mit `uv run fastapi dev` gestartet und alle Endpoints über `/docs` getestet. Als Hausaufgabe kamen die Endpoints `/square/{number}`, `/student` und `/double/{number}` dazu — dabei habe ich Path-Parameter und automatische Typkonvertierung von FastAPI kennengelernt.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Bei der Installation von `uv` unter Windows gab es anfangs das Problem, dass der Befehl nicht erkannt wurde, da der PATH noch nicht neu geladen war. Außerdem war mir zunächst unklar, warum `uv add fastapi` funktioniert, aber ein direktes `pip install` nicht denselben Effekt hat. Die Decorator-Syntax `@app.get("/")` war für mich neu — ich habe noch nicht verstanden, warum die Funktion darunter ohne expliziten Aufruf "wirkt".
 
---
 
#### 3. 💡 How did I overcome them?
 
Das PATH-Problem habe ich durch einen Neustart von VS Code gelöst. Den Unterschied zwischen `uv` und `pip` habe ich durch die Projektstruktur verstanden: `uv` legt ein isoliertes `.venv` an, sodass Abhängigkeiten projektspezifisch bleiben. Das Decorator-Konzept wurde mir klar, als ich in `/docs` gesehen habe, dass jeder neue Endpoint sofort ohne Neustart erscheint — FastAPI registriert die Funktion beim Import des Moduls, nicht beim Aufruf.
 
---
 
### Day 2
 
#### 1. ✅ What did I accomplish?
 
Tag 2 war der Einstieg in echte Datenpersistenz. Ich habe die Python-Grundlagen (Variablen, Datentypen, F-Strings, Funktionen mit Type Hints) aufgefrischt und parallel eine vollständige Note-Taking-API gebaut. Ich habe zwei Pydantic-Modelle definiert — `NoteCreate` für die Eingabe ohne ID und `Note` für die Ausgabe mit `id` und `created_at`. Die Endpoints `POST /notes` (Status 201), `GET /notes` und `GET /notes/{note_id}` inkl. 404-Behandlung via `HTTPException` habe ich implementiert. Der wichtigste Schritt war die Dateipersistenz: `load_notes()` liest `data/notes.json` beim Aufruf und berechnet den nächsten ID-Counter via `max(...)+1`, `save_notes()` schreibt nach jeder Änderung zurück. Als Hausaufgabe habe ich ein `category`-Feld ergänzt sowie einen Filter-Endpoint `/notes/category/{category}` und einen Statistik-Endpoint gebaut.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Die Persistenz war fehleranfälliger als erwartet. Mein erster Versuch führte zu doppelten IDs, weil der Counter nicht sauber mit der Datei synchronisiert war. Beim ersten Schreibversuch flog ein `FileNotFoundError`, da der `data/`-Ordner noch nicht existierte. Nach dem Hinzufügen des `category`-Felds hat Pydantic beim Laden alter JSON-Einträge (ohne dieses Feld) einen `ValidationError` geworfen.
 
---
 
#### 3. 💡 How did I overcome them?
 
Den ID-Konflikt habe ich behoben, indem `load_notes()` bei jedem Endpoint-Aufruf sowohl die Liste als auch den Counter aus der Datei liest — so ist die JSON-Datei immer die einzige Quelle der Wahrheit. Den `FileNotFoundError` habe ich mit `NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)` in `save_notes()` gelöst. Den Pydantic-Fehler habe ich pragmatisch durch Löschen der alten `notes.json` behoben — das hat mir erstmals das Thema Schema-Migration bewusst gemacht.
 
---
 
### Day 3
 
#### 1. ✅ What did I accomplish?
 
Tag 3 stand unter dem Motto REST-Design und vollständiges CRUD. Ich habe gelernt, dass URLs Ressourcen (Substantive) beschreiben sollen und HTTP-Methoden die Aktion ausdrücken. Meine Notes-API habe ich zur Version 2.0 erweitert: Tags als `list[str]` hinzugefügt, `GET /notes` um Query-Parameter `category`, `search` und `tag` erweitert (auch kombinierbar), `PUT /notes/{id}` (volle Ersetzung) und `DELETE /notes/{id}` mit Status 204 ergänzt. Dazu kamen die Tag-Ressourcen `GET /tags` und `GET /tags/{tag_name}/notes`. Als große Hausaufgabe habe ich die komplette Migration auf SQLite via SQLModel durchgeführt: Da SQLite keinen Array-Typ kennt, speichere ich Tags als CSV-String intern und konvertiere über `_tags_to_csv` / `_tags_to_list` an den API-Grenzen. Die Session-Dependency `SessionDep = Annotated[Session, Depends(get_session)]` ersetzt die alten `load_notes()`/`save_notes()`-Helfer. Außerdem habe ich PATCH mit `Optional`-Feldern und einen `created_after`/`created_before`-Datumsfilter implementiert.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Die Routing-Reihenfolge hat mich am meisten Zeit gekostet: Mein Endpoint `GET /notes/stats` wurde nie aufgerufen, weil FastAPI die Anfrage an `GET /notes/{note_id}` weiterleitete — `stats` wurde als Integer-Wert interpretiert und lieferte 422. Dasselbe Problem trat bei `DELETE /notes/duplicates` auf. Bei der SQLModel-Migration hatte ich einen `DetachedInstanceError`, weil ich nach `session.commit()` versucht habe, `note.tags` zu lesen, ohne vorher `session.refresh()` aufzurufen.
 
---
 
#### 3. 💡 How did I overcome them?
 
Das Routing-Problem habe ich gelöst, indem ich gelernt habe, dass FastAPI Routen in Definitionsreihenfolge matched: spezifische Pfade wie `/notes/stats` müssen vor dynamischen wie `/notes/{note_id}` stehen. Den `DetachedInstanceError` habe ich durch konsequentes `session.refresh(db_note)` nach jedem `commit()` behoben. Im Code habe ich einen Kommentar `# MUST be declared before /notes/{note_id}` hinzugefügt, damit dieser Fehler nicht wieder passiert.
 
---
 
## Week 2
 
### Day 4
 
#### 1. ✅ What did I accomplish?
 
An Tag 4 habe ich pytest kennengelernt und eine umfangreiche Test-Suite für meine Notes-API geschrieben. Ich habe beide Test-Ansätze ausprobiert: externe Tests mit der `requests`-Library gegen den laufenden Server und interne Tests mit dem `TestClient` von FastAPI. Das Arrange-Act-Assert-Schema habe ich verinnerlicht und Tests für CRUD-Operationen, kombinierte Filter, 404-Fehler, 422-Validierungsfehler und die Day-3-Features (Statistics, PATCH) geschrieben. Dazu habe ich `Faker` für zufällige Testdaten verwendet und die `clean_notes`-Fixture mit `tmp_path` und `monkeypatch.setattr(main, "engine", test_engine)` implementiert, die für jeden Test eine frische SQLite-Datenbank anlegt.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Test-Isolation war das größte Problem: Ohne Fixture haben Tests voneinander abgehangen, weil alle in dieselbe `notes.db` geschrieben haben. Beim ersten Lauf der requests-basierten Tests habe ich vergessen, den Server parallel zu starten und bekam einen `ConnectionError`. Bei DELETE-Endpoints war mir unklar, ob 200 oder 204 der richtige Statuscode ist.
 
---
 
#### 3. 💡 How did I overcome them?
 
Die Test-Isolation habe ich mit der `clean_notes`-Fixture gelöst: `monkeypatch.setattr(main, "engine", test_engine)` biegt die echte DB-Engine auf eine temporäre Datei um, sodass meine committete `notes.db` bei jedem Test-Lauf unangetastet bleibt. Das Zwei-Terminal-Pattern (Terminal 1: Server, Terminal 2: Tests) für requests-basierte Tests habe ich fest etabliert. Den Statuscode-Konflikt habe ich durch explizites `status_code=204` am Endpoint und `return Response(status_code=204)` gelöst.
 
---
 
### Day 5
 
#### 1. ✅ What did I accomplish?
 
Tag 5 war Pydantic-Validierung in der Tiefe. Ich habe `Field(...)` mit `min_length`, `max_length`, `pattern`, `ge`/`le` und `default_factory=list` eingesetzt. Mit `@field_validator` als `@classmethod` habe ich Felder normalisiert (`.strip().lower()`) und gegen eine Whitelist geprüft. Über `ConfigDict(str_strip_whitespace=True, extra="forbid")` habe ich modellweit Whitespace gestripped und unbekannte Felder (Tippfehler wie `tagz`) mit 422 abgelehnt. Ich habe eine zentrale Konstante `ALLOWED_CATEGORIES` und das Tag-Pattern `^[a-z0-9-]+$` als Single Source of Truth im Modul etabliert. Der `_normalize_tags`-Helper strippt, lowercased, dedupliziert und prüft Länge sowie maximale Anzahl. In `test_validation.py` habe ich Tests geschrieben, die prüfen, dass ungültige Eingaben zuverlässig mit 422 abgelehnt werden.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Bei `NoteUpdate` für PATCH war mir der Unterschied zwischen `Optional[str] = None` und einem Feld mit `min_length` nicht klar — meine erste Version hat `min_length` auch dann geprüft, wenn das Feld gar nicht mitgesendet wurde, sodass ein leeres `PATCH {}` mit 422 fehlschlug. Beim Tag-Validator habe ich `value.strip()` ohne `return` geschrieben, was Pydantic stillschweigend ignoriert hat.
 
---
 
#### 3. 💡 How did I overcome them?
 
Das `NoteUpdate`-Problem habe ich gelöst, indem ich verstanden habe, dass Pydantic Validierungen nur ausführt, wenn ein Feld tatsächlich einen Wert hat — `None` als Default wird nicht gegen `min_length` geprüft. Den Validator-Bug habe ich durch den rot gebliebenen Test entdeckt: nach Hinzufügen von `return value.strip().lower()` war der Test sofort grün. Die Folie "Always return the value" hat sich damit fest eingebrannt. Den `@model_validator(mode="after")` für die Cross-Field-Regel habe ich bewusst als kommentierten Showcase-Block im Code gelassen, da die Referenz-Test-Suite work-Notizen ohne work-Tag anlegt und ein aktiver Validator dort Tests brechen würde.
 
---
 
### Day 6
 
#### 1. ✅ What did I accomplish?
 
Tag 6 hatte zwei Schwerpunkte: eigene Decorators schreiben und die offizielle Test-Suite grün bekommen. In `Exploration/class_based_decorator.py` habe ich einen `Callcounter` (zählt Aufrufe mit `self.count`) und einen `Cache` (speichert Ergebnisse mit `(args, frozenset(kwargs.items()))` als Key und greift bei Cache-Hit darauf zurück) implementiert — beide nutzen `__call__` als Eintrittspunkt. Mit `icecream` (`ic()`) habe ich die Ausführung live nachverfolgt, was deutlich komfortabler als `print()` ist. Im zweiten Teil habe ich die offizielle `test_main.py` aus dem Kurs-Repo heruntergeladen, gegen meine API laufen lassen und alle roten Tests systematisch behoben: korrekter 204-Statuscode bei DELETE, alphabetisch sortierte und deduplizierte Tags, `top_tags` als `[{"tag": ..., "count": ...}]`-Struktur via `collections.Counter`.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Beim ersten Lauf der offiziellen Test-Suite hatte ich etwa ein Drittel rote Tests, obwohl meine eigenen Tests alle grün waren. Konkret hat das `tags`-Feld manchmal nicht dedupliziert geliefert, und das `/notes/stats`-Antwortschema stimmte nicht exakt mit der Erwartung der Suite überein. Beim klassenbasierten Decorator war mir the Unterschied zwischen Instanz-Erzeugung (`@MyDecorator`) und Funktionsaufruf (`__call__`) noch nicht klar.
 
---
 
#### 3. 💡 How did I overcome them?
 
Die roten Tests habe ich systematisch durchgegangen: für jeden roten Test zuerst die Assertion im Test-Code gelesen, dann den Endpoint angepasst. `ic()` hat mir beim Decorator-Verständnis enorm geholfen — durch `ic(self)` beim `__init__` und `ic(args, kwargs)` beim `__call__` wurde sichtbar, wann welcher Schritt ausgeführt wird. Offen geblieben ist für mich, wann man klassenbasierte Decorators gegenüber funktionsbasierten (mit `functools.wraps`) bevorzugen sollte.
 
---
 
## Week 3
 
### Day 7
 
#### 1. ✅ What did I accomplish?
 
Tag 7 war der Sprung ins Frontend mit Streamlit. Nach `uv add streamlit` habe ich zuerst eine "Hello World"-App und dann die "Say no"-App gebaut — ein Button, der per `requests.get` gegen `https://naas.isalman.dev/no` schickt und das `reason`-Feld aus der JSON-Antwort anzeigt. Dabei habe ich `st.session_state` als zentrales Konzept kennengelernt: Streamlit führt das Skript bei jeder Interaktion komplett neu aus, weshalb persistenter Zustand explizit in `session_state` abgelegt werden muss. Die Hausaufgabe — ein Streamlit-Frontend für meine Notes-API — habe ich mit zwei Funktionen implementiert: (1) alle Notes auflisten mit `st.expander(note["title"])` für den Detail-View und (2) eine neue Note anlegen über `st.form` mit einem einzigen Submit-Button für alle Felder (Titel, Content, Tags, Category).
 
---
 
#### 2. 🚧 What challenges did I face?
 
Das Streamlit-Ausführungsmodell hat mich anfangs komplett überrascht. Mein erster Versuch hat `notes = []` als normale Variable definiert — nach jedem Button-Klick war die Liste wieder leer. Ich habe versucht, jede Eingabe (Titel, Content, Tags, Category) mit einem eigenen Button zu bauen, was zu inkonsistentem Verhalten geführt hat. Beim API-Call gegen mein FastAPI-Backend bekam ich einen `ConnectionRefusedError`, weil ich das Backend nicht gestartet hatte.
 
---
 
#### 3. 💡 How did I overcome them?
 
Das Reload-Problem habe ich durch konsequente Nutzung von `st.session_state` gelöst — alles was einen Rerun überleben muss, kommt in den State mit dem Initialisierungsblock `if 'key' not in st.session_state`. Das Multi-Input-Problem habe ich mit `st.form` gelöst: innerhalb eines Form-Blocks lösen Eingabewidgets keine Reruns aus, alles wird erst beim `st.form_submit_button` gemeinsam abgeschickt. Den `ConnectionRefusedError` habe ich durch das konsequente Zwei-Terminal-Pattern behoben und den API-Call mit `try/except requests.exceptions.ConnectionError` abgesichert, sodass der User eine verständliche Fehlermeldung sieht. Die Komma-separierten Tags konvertiere ich mit `[t.strip() for t in tags_input.split(",") if t.strip()]` in eine saubere Liste — das Lowercasing übernimmt ohnehin der Pydantic-Validator im Backend.
 
---
 
### Day 8
 
#### 1. ✅ What did I accomplish?
 
An Tag 8 haben wir die Repo-Struktur finalisiert und offene Punkte für die Abgabe besprochen. Ich habe mein Repository aufgeräumt: `CLAUDE.md` als Architektur-Dokumentation erstellt, die `README.md` auf den aktuellen Stand (SQLite statt JSON) gebracht und die Test-Dateien sauber strukturiert. Außerdem habe ich nochmal alle Tests durchlaufen lassen und sichergestellt, dass sowohl die `TestClient`-basierten Tests als auch die requests-basierten Integrationstests (mit laufendem Server) grün sind.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Die Dokumentation hat mehr Zeit gekostet als erwartet — eine gute `CLAUDE.md`, die die Architektur korrekt und vollständig beschreibt, ist anspruchsvoller als ich dachte. Außerdem musste ich nochmal die Route-Reihenfolge prüfen, da ich einen neuen Endpunkt hinzugefügt hatte und der Routing-Konflikt von Tag 3 wieder aufgetaucht wäre.
 
---
 
#### 3. 💡 How did I overcome them?
 
Die `CLAUDE.md` habe ich strukturiert aufgebaut: erst Befehle, dann Architektur, dann kritische Design-Entscheidungen. Das Routing-Problem habe ich durch den bestehenden Kommentar im Code sofort erkannt und den neuen Endpoint an der richtigen Stelle eingefügt. Der Kurs hat mich insgesamt gelehrt, dass gute Dokumentation genauso wichtig ist wie der Code selbst.
 
---
 
### Day 9
 
#### 1. ✅ What did I accomplish?
 
Tag 9 war der Abschlusstag. Ich habe das Gesamtprojekt reviewt, die finale Abgabe vorbereitet und reflektiert, was ich in den drei Wochen gelernt habe: von den ersten FastAPI-Endpoints über Pydantic-Validierung, SQLModel-Datenbankanbindung und pytest-Tests bis hin zum Streamlit-Frontend. Das Projekt hat mir gezeigt, wie man eine vollständige, produktionsreife Web-API von Grund auf aufbaut.
 
---
 
#### 2. 🚧 What challenges did I face?
 
Die größte Herausforderung des gesamten Kurses war für mich das Zusammenspiel aller Schichten: Frontend (Streamlit) → API (FastAPI) → Validierung (Pydantic) → Datenbank (SQLModel/SQLite). Besonders die Fehlerbehandlung über alle Schichten hinweg — ein 422-Fehler aus Pydantic muss im Frontend verständlich angezeigt werden — war hochgradig komplex.
 
---
 
#### 3. 💡 How did I overcome them?
 
Durch das schrittweise Vorgehen in den Kurstagen — jeder Tag hat auf dem vorherigen aufgebaut — war die Komplexität handhabbar. Die Test-Suite hat mir geholfen, Regressionen und Fehler beim Umbauen sofort zu erkennen. Rückblickend war die Entscheidung, Tags als CSV in SQLite zu speichern und an den API-Grenzen zu konvertieren, pragmatisch absolut richtig für dieses Projekt — in einem größeren Produktionssystem würde ich eine separate Tags-Tabelle mit einer echten Many-to-Many-Beziehung bevorzugen.
 
---