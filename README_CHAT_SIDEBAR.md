# Chat-Sidebar Baustein für NiceGUI + Ollama (≤8B)

Dieser Baustein ergänzt eine bestehende NiceGUI-App um ein einklappbares Chat-Panel (rechter Drawer) mit lokalem Ollama-Modell. Bestehende Dateien bleiben unverändert.

Installation (nur für den Baustein):

- `pip install -r requirements-chat.txt`
- Stelle sicher, dass Ollama installiert und ein lokales Modell verfügbar ist (z. B. `ollama run llama3:8b`).

Einbindung in bestehende App (Beispiel):

```python
# Beispiel: Integration in bestehende UI (nicht überschreiben!)
from nicegui import ui
from chat_sidebar import mount_chat_sidebar
import os

@ui.page('/')
def main_page():
    with ui.row().classes('w-full items-center justify-between'):
        ui.label('Meine bestehende App')
    # Inhalt deiner App …
    sidebar = mount_chat_sidebar(ui)  # an Root/aktuelle Seite montieren
    # FAB unten rechts:
    with ui.element('div').classes('fixed bottom-6 right-6'):
        ui.button(icon='chat', on_click=sidebar['toggle']).props('round unelevated size=lg')

if __name__ == '__main__':
    # Beispiel: ENV
    os.environ.setdefault('LLM_MODEL', 'llama3:8b')
    ui.run()
```

Hinweise
- Standardmodell: `LLM_MODEL` (ENV), Fallback: `llama3:8b`.
- Streaming, Stop, Reset und Zeitstempel sind integriert.
- Bei fehlendem/gestopptem Ollama wird ein klarer Fehlerhinweis in der Sidebar angezeigt.
- Der Baustein startet keinen eigenen Server und kann auf jeder Seite montiert werden.
