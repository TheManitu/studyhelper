import streamlit as st
import datetime
import json
import os
import time
import pandas as pd

# Dateipfade für Persistenz
tasks_file = 'tasks.json'
plan_file = 'study_plan.json'

# Sounds
END_SOUND = 'https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3'
BEEP_SOUND = 'https://www.soundjay.com/button/sounds/beep-07.mp3'

# Lade-/Speicherfunktionen
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# Session State Defaults
if 'tasks_data' not in st.session_state:
    st.session_state.tasks_data = load_json(tasks_file, {'date': str(datetime.date.today()), 'tasks': []})
if 'plan_data' not in st.session_state:
    st.session_state.plan_data = load_json(plan_file, {'entries': []})
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'end_time' not in st.session_state:
    st.session_state.end_time = None
if 'beep_played' not in st.session_state:
    st.session_state.beep_played = False

st.title("📝 Studien-Unterstützer")

# 1. Tägliche Routinen
st.header("Tägliche Routinen")
tasks = st.session_state.tasks_data
today = str(datetime.date.today())
if tasks.get('date') != today:
    for t in tasks['tasks']:
        t['done'] = False
    tasks['date'] = today
    save_json(tasks_file, tasks)

with st.form('add_task'):
    new_task = st.text_input('Neue Routine')
    if st.form_submit_button('Hinzufügen') and new_task:
        tasks['tasks'].append({'name': new_task, 'done': False})
        save_json(tasks_file, tasks)

for i, t in enumerate(tasks['tasks']):
    c1, c2 = st.columns([0.8, 0.2])
    chk = c1.checkbox(t['name'], value=t['done'], key=f"task_{i}")
    if chk != t['done']:
        tasks['tasks'][i]['done'] = chk
        save_json(tasks_file, tasks)
    if c2.button('🗑️', key=f"del_task_{i}"):
        tasks['tasks'].pop(i)
        save_json(tasks_file, tasks)
        break

st.markdown('---')

# 2. Pomodoro-Timer
st.header("⏱️ Pomodoro-Timer")
duration = st.number_input('Dauer (Minuten)', min_value=1, value=25, step=1)

col_start, col_stop = st.columns(2)
with col_start:
    if (not st.session_state.timer_running) and st.button('Start Timer', key='start_timer'):
        st.session_state.end_time = time.time() + duration * 60
        st.session_state.beep_played = False
        st.session_state.timer_running = True
with col_stop:
    if st.session_state.timer_running and st.button('Stop Timer', key='stop_timer'):
        st.session_state.timer_running = False
        st.session_state.end_time = None
        st.session_state.beep_played = False

# Timer-Anzeige und Loop
timer_ph = st.empty()
if st.session_state.timer_running and st.session_state.end_time:
    while st.session_state.timer_running:
        rem = int(st.session_state.end_time - time.time())
        if rem <= 0:
            break
        m, s = divmod(rem, 60)
        timer_ph.markdown(
            f"<h1 style='font-size:8vw;text-align:center;'>{m:02d}:{s:02d}</h1>",
            unsafe_allow_html=True
        )
        if (rem <= 5) and (not st.session_state.beep_played):
            timer_ph.markdown(
                f'<audio autoplay src="{BEEP_SOUND}"></audio>',
                unsafe_allow_html=True
            )
            st.session_state.beep_played = True
        time.sleep(1)
    # Am Ende 00:00 anzeigen
    timer_ph.markdown(
        "<h1 style='font-size:8vw;text-align:center;'>00:00</h1>",
        unsafe_allow_html=True
    )
    # End-Sound 10min
    start_ts = time.time()
    while time.time() - start_ts < 600:
        timer_ph.markdown(
            f'<audio autoplay loop src="{END_SOUND}"></audio>',
            unsafe_allow_html=True
        )
        time.sleep(1)
    # Reset
    st.session_state.timer_running = False
    st.session_state.end_time = None
    st.session_state.beep_played = False

st.markdown('---')

# 3. Lernplan bis zur nächsten Klausur
st.header("🎯 Lernplan bis zur nächsten Klausur")
entries = st.session_state.plan_data['entries']

# Delete index flag
if 'delete_idx' not in st.session_state:
    st.session_state.delete_idx = None

# Detect button presses
for idx, entry in enumerate(entries.copy()):
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 3, 0.5])
    # Editable fields
    nt = c1.text_input('Aufgabe', value=entry.get('Aufgabe', ''), key=f'aufgabe_{idx}')
    # Parse date with fallback
    date_str = entry.get('Fälligkeitsdatum', '')
    try:
        default_date = datetime.date.fromisoformat(date_str)
    except:
        default_date = datetime.date.today()
    nd = c2.date_input('Fälligkeitsdatum', value=default_date, key=f'datum_{idx}')
    ndone = c3.checkbox('Erledigt', value=entry.get('Erledigt', False), key=f'erledigt_{idx}')
    notes = c4.text_input('Notizen', value=entry.get('Notizen', ''), key=f'notizen_{idx}')
    if c5.button('🗑️', key=f'del_plan_{idx}'):
        st.session_state.delete_idx = idx
    # Save changes
    if (nt != entry.get('Aufgabe') or
        str(nd) != entry.get('Fälligkeitsdatum') or
        ndone != entry.get('Erledigt') or
        notes != entry.get('Notizen')):
        entries[idx] = {
            'Aufgabe': nt,
            'Fälligkeitsdatum': str(nd),
            'Erledigt': ndone,
            'Notizen': notes
        }
        save_json(plan_file, {'entries': entries})
# Perform deletion after rendering all rows
if st.session_state.delete_idx is not None:
    del entries[st.session_state.delete_idx]
    save_json(plan_file, {'entries': entries})
    st.session_state.delete_idx = None
    st.experimental_rerun = None
    st.experimental_rerun = None
st.markdown('---')
# Add new entry
with st.form('add_plan'):
    ntw = st.text_input('Neue Aufgabe')
    ndw = st.date_input('Fälligkeitsdatum', value=datetime.date.today(), key='add_date')
    notesw = st.text_input('Notizen', key='add_notes')
    if st.form_submit_button('Hinzufügen') and ntw:
        entries.append({'Aufgabe': ntw, 'Fälligkeitsdatum': str(ndw), 'Erledigt': False, 'Notizen': notesw})
        save_json(plan_file, {'entries': entries})
        st.success('Eintrag hinzugefügt!')
