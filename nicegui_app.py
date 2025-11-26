from nicegui import ui
from nicegui import events
from nicegui import app
from fastapi.responses import FileResponse
from chat_sidebar import mount_chat_sidebar


# Statische Logout-Seite direkt über FastAPI ausliefern (ohne NiceGUI-Assets)
@app.get('/logged-out.html')
def _logged_out_static():
    return FileResponse('web/logged-out.html', media_type='text/html')

# --- NiceGUI UI ---
def build_ui():
    # Layout and styles
    ui.add_head_html('<meta http-equiv="Cache-Control" content="no-store" />')
    # Tailwind via CDN + Custom Animations/Theming
    ui.add_head_html('''
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
      tailwind.config = {
        theme: {
          extend: {
            fontFamily: { display: ['Inter', 'ui-sans-serif', 'system-ui'] },
            colors: {
              brand: {
                50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc',
                400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca',
                800: '#3730a3', 900: '#312e81'
              }
            },
            keyframes: {
              floaty: { '0%,100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-4px)'} },
              glow: {
                '0%,100%': { boxShadow: '0 0 0px rgba(99,102,241,0.0)' },
                '50%': { boxShadow: '0 0 24px rgba(99,102,241,0.35)' }
              },
              fadein: { '0%': { opacity: 0, transform: 'translateY(6px)' }, '100%': { opacity: 1, transform: 'translateY(0)'} },
              gradient: {
                '0%': { backgroundPosition: '0% 50%' },
                '50%': { backgroundPosition: '100% 50%' },
                '100%': { backgroundPosition: '0% 50%' }
              },
              tickpop: {
                '0%': { transform: 'translateY(0) scale(1)', filter: 'brightness(1)' },
                '35%': { transform: 'translateY(-2px) scale(1.06)', filter: 'brightness(1.05)' },
                '100%': { transform: 'translateY(0) scale(1)', filter: 'brightness(1)' }
              },
              cardin: { '0%': { opacity: 0, transform: 'translateY(8px) scale(.98)' }, '100%': { opacity: 1, transform: 'translateY(0) scale(1)' } }
            },
            animation: {
              floaty: 'floaty 4s ease-in-out infinite',
              glow: 'glow 4s ease-in-out infinite',
              fadein: 'fadein 320ms ease-out both',
              gradient: 'gradient 12s ease infinite',
              tick: 'tickpop 260ms ease-out both',
              cardin: 'cardin 380ms ease-out both'
            }
          }
        }
      }
    </script>
    <style>
      /* Tailwind CDN does not support @apply; inline classes instead in components. */
      .gradient-bar { background: linear-gradient(90deg, #6366f1, #22d3ee, #a78bfa); background-size: 200% 200%; }
      .bg-hero { background: radial-gradient(1000px 600px at -10% -10%, rgba(99,102,241,0.25), transparent 60%), radial-gradient(900px 500px at 110% -10%, rgba(34,211,238,0.22), transparent 60%), radial-gradient(1100px 700px at 50% 120%, rgba(167,139,250,0.22), transparent 60%); }
      .card-accent { position: relative; overflow: hidden; }
      .card-accent::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 3px; background: linear-gradient(90deg, #6366f1, #22d3ee, #a78bfa); background-size: 200% 200%; animation: gradient 12s ease infinite; }
    </style>
    <script>
      document.addEventListener('DOMContentLoaded', () => { document.body.classList.add('bg-hero'); });
    </script>
    ''')

    with ui.header().classes('justify-between items-center q-pa-md bg-white/70 backdrop-blur-md border-b border-black/5 sticky top-0 z-[1000]'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('school').classes('text-brand-600 text-2xl animate-glow')
            ui.label('StudyHelper').classes('text-h5 text-bold font-display')
        with ui.row().classes('items-center gap-3'):
            # RP-initiated Logout: über oauth2-proxy zu Keycloak end_session leiten,
            # danach zurück auf die öffentliche Logout-Seite der App
            # rd muss als Query-Parameter URL-encoded sein (komplette Logout-URL doppelt encodet)
            # Innerer Logout (studyhelper, Client oauth2-proxy):
            #   http://localhost:8080/realms/studyhelper/protocol/openid-connect/logout?client_id=oauth2-proxy&post_logout_redirect_uri=http%3A%2F%2Flocalhost%3A8081%2Flogged-out.html
            # rd (äußere Encodierung):
            rd = 'http%3A%2F%2Flocalhost%3A8080%2Frealms%2Fstudyhelper%2Fprotocol%2Fopenid-connect%2Flogout%3Fclient_id%3Doauth2-proxy%26post_logout_redirect_uri%3Dhttp%253A%252F%252Flocalhost%253A8081%252Flogged-out.html'
            ui.link('Logout', f'/oauth2/sign_out?rd={rd}').classes('bg-white/60 hover:bg-white/80 text-slate-700 transition-all duration-200 px-3 py-1.5 rounded-lg')

    # Main wrapper: viewport nutzen, zentriert, Padding 80px
    with ui.element('main').classes('min-h-screen p-20'):
        container = ui.element('div').classes('max-w-7xl mx-auto w-full')
        with container:
            # Hero
            with ui.element('section').classes('mb-8 animate-fadein'):
                with ui.row().classes('items-end justify-between'):
                    with ui.column():
                        ui.label('Dein Lern-Cockpit').classes('text-2xl md:text-3xl font-semibold text-slate-800')
                        ui.label('Plane, fokussiere, erreiche mehr – mit Stil.').classes('text-slate-500')
                    ui.element('div').classes('h-1 w-48 rounded-full gradient-bar animate-gradient opacity-70')
            # Grid
            grid = ui.element('div').classes('grid grid-cols-12 gap-6 animate-fadein')

        # To-Do Karte
        with grid:
            with ui.card().classes('bg-white/80 backdrop-blur-xl ring-1 ring-black/5 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-xl hover:-translate-y-0.5 card-accent w-full p-6 animate-cardin col-span-12 md:col-span-4'):
                ui.label('To‑Do Liste').classes('text-slate-800 font-semibold tracking-tight')
                new_task = ui.input(placeholder='Neue Aufgabe').classes('w-full').style('color:black; background:white;')
                tasks = ui.column().classes('gap-2 mt-2')

                def add_task():
                    t = new_task.value.strip() if new_task.value else ''
                    if not t:
                        return
                    with tasks:
                        with ui.row().classes('items-center justify-between q-px-none').style('width:100%') as row:
                            cb = ui.checkbox(value=False)
                            label = ui.label(t)
                            label.style('max-width: 70%;')
                            def on_change(e):
                                label.style('text-decoration: line-through; opacity:0.7' if cb.value else '')
                                try:
                                    current = int(done_label.text)
                                except Exception:
                                    current = 0
                                if cb.value:
                                    current += 1
                                elif current > 0:
                                    current -= 1
                                done_label.text = str(current)
                            cb.on('change', on_change)
                            ui.button('Löschen', on_click=lambda r=row: r.delete()).props('flat').classes('bg-white/60 hover:bg-white/80 text-slate-700 transition-all duration-200 px-2 py-1 rounded-md')
                    new_task.value = ''

                ui.button('Hinzufügen', on_click=add_task).classes('bg-brand-600 hover:bg-brand-700 text-white transition-all duration-200 px-3 py-1.5 rounded-md')

        # Termine Karte
        with grid:
            with ui.card().classes('bg-white/80 backdrop-blur-xl ring-1 ring-black/5 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-xl hover:-translate-y-0.5 card-accent w-full p-6 animate-cardin col-span-12 md:col-span-4'):
                ui.label('Wichtige Termine').classes('text-slate-800 font-semibold tracking-tight')
                desc = ui.input(placeholder='Beschreibung').classes('w-full').style('color:black; background:white;')
                date = ui.input(label='Datum').props('type=date').classes('w-full').style('color:black; background:white;')
                dates_col = ui.column().classes('gap-2')

                def add_date():
                    d = (date.value or '').strip()
                    x = (desc.value or '').strip()
                    if not x:
                        return
                    with dates_col:
                        with ui.row().classes('items-center justify-between').style('width:100%') as row:
                            ui.label(f'{d or "—"} – {x}')
                            ui.button('Löschen', on_click=lambda r=row: r.delete()).props('flat').classes('bg-white/60 hover:bg-white/80 text-slate-700 transition-all duration-200 px-2 py-1 rounded-md')
                    desc.value = ''

                ui.button('Speichern', on_click=add_date).classes('bg-brand-600 hover:bg-brand-700 text-white transition-all duration-200 px-3 py-1.5 rounded-md')

        # Achievements Karte
        with grid:
            with ui.card().classes('bg-white/80 backdrop-blur-xl ring-1 ring-black/5 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-xl hover:-translate-y-0.5 card-accent w-full p-6 animate-cardin col-span-12 md:col-span-4'):
                ui.label('Achievements').classes('text-slate-800 font-semibold tracking-tight')
                with ui.column().classes('space-y-2 mt-1'):
                    with ui.row().classes('items-center'):
                        ui.label('Erledigte Aufgaben:').classes('text-slate-500')
                        done_label = ui.label('0').classes('text-weight-bold text-brand-600')
                    with ui.row().classes('items-center'):
                        ui.label('Pomodoros abgeschlossen:').classes('text-slate-500')
                        pomos_label = ui.label('0').classes('text-weight-bold text-brand-600')

        # Pomodoro Karte (volle Breite)
        with grid:
            with ui.card().classes('bg-white/80 backdrop-blur-xl ring-1 ring-black/5 rounded-2xl transition-all duration-300 shadow-sm hover:shadow-xl hover:-translate-y-0.5 card-accent w-full p-6 animate-cardin col-span-12'):
                ui.label('Pomodoro Timer').classes('text-slate-800 font-semibold tracking-tight')
                display = ui.label('25:00').classes('text-6xl font-mono text-slate-800 tracking-tight')
                with ui.row().classes('items-center gap-3'):
                    work = ui.input(value='25', label='Arbeit (min)').style('color:black; background:white; width:120px').props('type=number min=1')
                    brk = ui.input(value='5', label='Pause (min)').style('color:black; background:white; width:120px').props('type=number min=1')
                phase = ui.label('Phase: Arbeit').classes('text-slate-500')

                import asyncio
                running = {'val': False}
                remaining = {'sec': 25*60}
                current_phase = {'val': 'work'}

                def fmt(sec:int) -> str:
                    m, s = divmod(max(0, int(sec)), 60)
                    return f'{m:02d}:{s:02d}'

                # tick animation toggle state
                tick_state = {'a': False}

                def tick_pop():
                    base = 'text-6xl font-mono text-slate-800 tracking-tight '
                    anim = 'animate-tick' if tick_state['a'] else 'animate-none'
                    display.classes(base + anim)
                    tick_state['a'] = not tick_state['a']

                async def tick():
                    while running['val']:
                        await asyncio.sleep(1)
                        remaining['sec'] -= 1
                        if remaining['sec'] <= 0:
                            if current_phase['val'] == 'work':
                                current_phase['val'] = 'break'
                                remaining['sec'] = max(60, int((brk.value or '5'))*60)
                                try:
                                    p = int(pomos_label.text)
                                except Exception:
                                    p = 0
                                p += 1
                                pomos_label.text = str(p)
                            else:
                                current_phase['val'] = 'work'
                                remaining['sec'] = max(60, int((work.value or '25'))*60)
                            phase.text = f'Phase: {"Arbeit" if current_phase["val"]=="work" else "Pause"}'
                        display.text = fmt(remaining['sec'])
                        tick_pop()

                def start():
                    if not running['val']:
                        running['val'] = True
                        ui.timer(0.1, tick, once=True)

                def pause():
                    running['val'] = False

                def reset():
                    pause()
                    current_phase['val'] = 'work'
                    remaining['sec'] = max(60, int((work.value or '25'))*60)
                    display.text = fmt(remaining['sec'])
                    phase.text = 'Phase: Arbeit'

                with ui.row().classes('gap-2 mt-2'):
                    ui.button('Start', on_click=start).classes('bg-brand-600 hover:bg-brand-700 text-white transition-all duration-200 px-3 py-1.5 rounded-md')
                    ui.button('Pause', on_click=pause).classes('bg-white/60 hover:bg-white/80 text-slate-700 transition-all duration-200 px-3 py-1.5 rounded-md')
                    ui.button('Reset', on_click=reset).classes('bg-white/60 hover:bg-white/80 text-slate-700 transition-all duration-200 px-3 py-1.5 rounded-md')

                reset()


@ui.page('/')
def index_page():
    build_ui()
    # Chat-Sidebar montieren und FAB hinzufügen
    sidebar = mount_chat_sidebar(ui)
    with ui.element('div').classes('fixed bottom-6 right-6 animate-floaty z-[11000]'):
        ui.button(icon='chat', on_click=lambda: sidebar['toggle']()).props('round unelevated size=lg').classes('shadow-xl hover:shadow-2xl transition-transform hover:-translate-y-0.5')


# Hinweis: /logged-out.html kommt als reine statische Seite aus dem Ordner 'web'.


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(host='0.0.0.0', port=8081, reload=False)
