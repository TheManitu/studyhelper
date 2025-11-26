from __future__ import annotations

import asyncio
import threading
import contextlib
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args: Any, **kwargs: Any) -> None:  # fallback no-op
        return None

from nicegui import ui


def _now_time() -> str:
    return datetime.now().strftime('%H:%M')


def mount_chat_sidebar(
    page: Any,
    *,
    model_env_var: str = "LLM_MODEL",
    default_model: str = "llama3:8b",
    drawer_width: int = 420,
    title: str = "StudyHelper Chat",
    system_prompt: Optional[str] | None = None,
):
    """Bindet eine einklappbare Chat-Sidebar an die gegebene NiceGUI-Page an.

    Rückgabe: dict mit Schlüsseln {"toggle", "elements", "get_history", "set_history"}.
    - page: NiceGUI page oder content area, z.B. ui.page("/") oder ui.column().
    - toggle(): callable zum Öffnen/Schließen, wird auch vom FAB verwendet.
    """

    load_dotenv()  # optional .env laden, falls vorhanden

    # Lazy import von ollama, um ImportError kontrolliert zu behandeln
    ollama: Optional[Any] = None
    ollama_import_error: Optional[Exception] = None
    try:
        import ollama as _ollama  # type: ignore

        ollama = _ollama
    except Exception as e:  # pragma: no cover
        ollama_import_error = e

    model_name = os.getenv(model_env_var, default_model) or default_model

    # Session-lokaler Verlauf inkl. system prompt
    history: List[Dict[str, str]] = []

    if not system_prompt:
        system_prompt = (
            "Du bist ein kurzer, präziser StudyHelper im Q&A-Stil. "
            "Antworte knapp, strukturiert, mit kleinen Beispielen. "
            "Frage bei Unklarheit genau eine Rückfrage. "
            "Wenn Info fehlt, sag es ehrlich."
        )

    # Flags und Laufzeitstatus
    stop_event: threading.Event = threading.Event()
    is_streaming: bool = False
    model_ready: bool = False
    model_error: Optional[str] = None

    # Hilfsfunktionen
    def ensure_system_prompt() -> None:
        if not history or history[0].get("role") != "system":
            history.insert(0, {"role": "system", "content": system_prompt or ""})

    async def ensure_model() -> None:
        nonlocal model_ready, model_error
        if model_ready:
            return
        if ollama is None:
            model_error = (
                "Python-Paket 'ollama' nicht installiert. Installiere mit 'pip install ollama'."
            )
            return
        try:
            # pull im Thread, um UI nicht zu blockieren
            await asyncio.to_thread(ollama.pull, model_name)
            model_ready = True
            model_error = None
        except Exception as e:  # pragma: no cover
            model_ready = False
            model_error = (
                f"Ollama nicht erreichbar oder Pull fehlgeschlagen: {e}. "
                "Installieren/Starten: https://ollama.com • Beispiel: 'ollama run "
                f"{model_name}'."
            )

    def scroll_to_bottom() -> None:
        # Scrollt den Chat-Container ans Ende
        try:
            ui.run_javascript(
                "element.scrollTop = element.scrollHeight;",
                element=chat_column,
            )
        except Exception:
            pass

    def bubble(role: str, text: str = "", time_suffix: Optional[str] = None):
        """Erzeuge eine moderne Chat-Bubble; gibt (wrapper_row, content_label, meta_label) zurück."""
        align_class = "justify-end" if role == "user" else "justify-start"
        if role == "user":
            bubble_classes = (
                "bg-gradient-to-r from-brand-600 to-cyan-500 text-white"
            )
        else:
            bubble_classes = (
                "bg-white/80 dark:bg-gray-800/80 text-slate-800 dark:text-white backdrop-blur-xl ring-1 ring-black/5"
            )
        with ui.row().classes(f"w-full {align_class}") as row:
            with ui.column().classes("max-w-[85%] gap-1 animate-fadein"):
                with ui.card().classes(f"px-3 py-2 rounded-2xl shadow {bubble_classes}"):
                    content = ui.label(text).classes("whitespace-pre-wrap break-words")
                meta = ui.label((time_suffix or _now_time())).classes("text-xs text-gray-500 self-end pr-1")
        return row, content, meta

    async def send(user_text: str) -> None:
        nonlocal is_streaming
        if is_streaming:
            return
        if not user_text.strip():
            return

        # reset stop flag
        stop_event.clear()
        is_streaming = True
        btn_send.disable()
        btn_stop.enable()
        user_input.disable()

        ensure_system_prompt()
        # UI: User-Bubble
        bubble("user", user_text)
        scroll_to_bottom()
        history.append({"role": "user", "content": user_text})

        # UI: Assistant-Bubble (leer zum Streamen)
        a_row, a_label, a_meta = bubble("assistant", "")
        scroll_to_bottom()

        # Early check: Modell/Backend
        await ensure_model()
        if model_error:
            ui.notify(model_error, type="negative")
            a_label.text = (
                "[Fehler] Ollama nicht erreichbar. Installiere/Starte Ollama, z. B. "
                f"'ollama run {model_name}'."
            )
            a_label.update()
            is_streaming = False
            btn_send.enable()
            btn_stop.disable()
            user_input.enable()
            user_input.set_value("")
            return

        # Stream vom Modell
        full_assistant_text: str = ""
        started = asyncio.get_event_loop().time()
        token_count = 0

        queue: asyncio.Queue = asyncio.Queue()

        def producer(loop: asyncio.AbstractEventLoop) -> None:
            nonlocal token_count
            try:
                assert ollama is not None
                stream = ollama.chat(
                    model=model_name,
                    messages=history,
                    stream=True,
                )
                for chunk in stream:
                    if stop_event.is_set():
                        break
                    if isinstance(chunk, dict):
                        msg = chunk.get("message") or {}
                        delta = msg.get("content", "")
                        if delta:
                            token_count += 1
                            asyncio.run_coroutine_threadsafe(
                                queue.put(("delta", delta)), loop
                            )
                        if chunk.get("done"):
                            break
            except Exception as e:
                asyncio.run_coroutine_threadsafe(queue.put(("error", str(e))), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(("done", None)), loop)

        loop = asyncio.get_event_loop()
        # Start producer in background thread
        producer_task = asyncio.create_task(asyncio.to_thread(producer, loop))

        # Consume queue in main loop
        try:
            while True:
                kind, payload = await queue.get()
                if kind == "delta":
                    full_assistant_text += payload
                    a_label.text = full_assistant_text
                    a_label.update()
                    scroll_to_bottom()
                elif kind == "error":
                    a_label.text = (
                        "[Fehler] Beim Abruf von Ollama ist ein Fehler aufgetreten: "
                        f"{payload}\nBitte stelle sicher, dass der Ollama-Dienst läuft und das Modell "
                        f"'{model_name}' verfügbar ist (z. B. 'ollama run {model_name}')."
                    )
                    a_label.update()
                elif kind == "done":
                    break
        finally:
            # warte auf Producer-Ende (best-effort)
            with contextlib.suppress(Exception):
                await producer_task
            # Ergebnis in Verlauf übernehmen (ggf. abgebrochen)
            if full_assistant_text:
                history.append({"role": "assistant", "content": full_assistant_text})

            # kleine Latenz-/Token-Anzeige (optional)
            elapsed_s = max(0.0, asyncio.get_event_loop().time() - started)
            a_meta.text = f"{_now_time()} • ⏱ {elapsed_s:.1f}s • tkn {token_count}"
            a_meta.update()

            is_streaming = False
            btn_send.enable()
            btn_stop.disable()
            user_input.enable()
            user_input.set_value("")
            scroll_to_bottom()

    def reset_chat() -> None:
        history.clear()
        chat_column.clear()
        # optional: Hinweis
        with chat_column:
            ui.label("Neuer Chat gestartet.").classes("text-xs text-gray-500")
        scroll_to_bottom()

    def stop_stream() -> None:
        stop_event.set()

    def toggle_drawer() -> None:
        drawer.value = not drawer.value
        drawer.update()

    def get_history() -> List[Dict[str, str]]:
        return list(history)

    def set_history(new_history: List[Dict[str, str]]) -> None:
        history.clear()
        history.extend(new_history)
        chat_column.clear()
        for m in history:
            if m.get("role") == "system":
                continue
            role = m.get("role", "assistant")
            text = m.get("content", "")
            bubble(role, text)
        scroll_to_bottom()

    # UI-Aufbau innerhalb der angegebenen Page/Section (wenn möglich)
    if hasattr(page, "__enter__") and hasattr(page, "__exit__"):
        ctx = page
    else:
        # Fallback: kein Kontextmanager (z. B. 'ui' selbst)
        class _Dummy:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        ctx = _Dummy()

    with ctx:
        with ui.right_drawer(
            value=False, fixed=True, elevated=True
        ) as drawer:
            # Breite über Quasar-Prop setzen (NiceGUI <1.5 akzeptiert kein width-kwarg)
            drawer.props(f"width={drawer_width} overlay")
            drawer.classes("z-[9999]")
            # Header
            with ui.row().classes("items-center justify-between px-3 py-2"):
                ui.label(title).classes("text-md font-semibold")
                with ui.row().classes("items-center gap-2"):
                    model_badge = ui.badge(model_name).props("color=primary outline")
                    btn_reset = ui.button(
                        "Neu starten", icon="refresh", on_click=reset_chat
                    ).props("flat")
                    btn_stop = ui.button("Stop", icon="stop", on_click=stop_stream).props(
                        "flat"
                    )
                    btn_stop.disable()

            # Fehlerhinweisbereich (wenn ollama fehlt)
            if ollama_import_error is not None:
                with ui.card().classes("m-2 bg-red-1 text-red-8"):
                    ui.label(
                        "Ollama-Pythonpaket fehlt. Bitte 'pip install ollama' ausführen."
                    )

            # Chatbereich
            chat_column = ui.column().classes(
                "gap-2 px-2 py-2 overflow-y-auto h-[calc(100vh-240px)]"
            )

            # Eingabezeile
            with ui.row().classes("items-center gap-2 p-2 border-t"):
                user_input = ui.input(
                    placeholder="Frage eingeben und Enter drücken...",
                ).props("clearable filled dense").classes("w-full")
                btn_send = ui.button("Senden", icon="send").props("unelevated")

        # Input-Events
        user_input.on("keydown.enter", lambda e: ui.run(send(user_input.value)))
        btn_send.on("click", lambda e: ui.run(send(user_input.value)))

    # Auto-Pull im Hintergrund anstoßen (ohne zu blockieren)
    async def _background_pull():
        await ensure_model()
        # Bei Fehler: roten Hinweis im Drawer zeigen
        if model_error:
            with drawer:
                with ui.card().classes("m-2 bg-red-1 text-red-8"):
                    ui.label(
                        "Ollama nicht erreichbar. Installation/Start: https://ollama.com • "
                        f"Beispiel: 'ollama run {model_name}'."
                    )

    # Timer, um nach Mount zu starten
    ui.timer(0.1, _background_pull, once=True)

    # Erste Info im Chat
    with chat_column:
        ui.label(
            "Willkommen! Stelle eine Frage an das lokale Modell."
        ).classes("text-xs text-gray-500")

    return {
        "toggle": toggle_drawer,
        "elements": {
            "drawer": drawer,
            "container": chat_column,
            "input": user_input,
            "btn_send": btn_send,
            "btn_reset": btn_reset,
            "btn_stop": btn_stop,
            "model_badge": model_badge,
        },
        "get_history": get_history,
        "set_history": set_history,
    }
