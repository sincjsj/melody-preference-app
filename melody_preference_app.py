# melody_preference_app.py
import streamlit as st
import random
import datetime
import sqlite3
import numpy as np
import pandas as pd

# --- 설정 ---
TEMPO = 100  # BPM
DURATION_DENOMS = [1, 2, 3, 4, 6, 8]
BEATS_PER_BAR = 4
TOTAL_BARS = 4
TOTAL_BEATS = BEATS_PER_BAR * TOTAL_BARS  # 16박자
DURATION_BEATS = {d: BEATS_PER_BAR / d for d in DURATION_DENOMS}
SAMPLE_RATE = 44100  # Hz

# E3–E4 크로매틱 반음계
CHROMATIC = [
    ('E3', 164.81), ('F3', 174.61), ('F#3', 185.00), ('G3', 196.00), ('G#3', 207.65),
    ('A3', 220.00), ('A#3', 233.08), ('B3', 246.94), ('C4', 261.63), ('C#4', 277.18),
    ('D4', 293.66), ('D#4', 311.13), ('E4', 329.63)
]
NOTE_NAMES, NOTE_FREQS = zip(*CHROMATIC)

# --- DB 초기화 ---
conn = sqlite3.connect('melody_preferences.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS preferences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  melody_a TEXT,
  melody_b TEXT,
  preferred TEXT,
  timestamp TEXT
)
''')
conn.commit()

# --- 멜로디 생성 ---
def generate_melody():
    melody = []
    beats_left = TOTAL_BEATS
    while beats_left > 0:
        d = random.choice(DURATION_DENOMS)
        b = DURATION_BEATS[d]
        if b <= beats_left:
            note = random.choice(NOTE_NAMES)
            melody.append((note, d))
            beats_left -= b
    return melody

# --- NumPy 배열로 오디오 만들기 ---
@st.cache_data
def melody_to_array(melody):
    audio = np.zeros(0, dtype=np.int16)
    for note, d in melody:
        length = (60/TEMPO)*DURATION_BEATS[d]
        samples = int(SAMPLE_RATE*length)
        t = np.linspace(0, length, samples, endpoint=False)
        freq = NOTE_FREQS[NOTE_NAMES.index(note)]
        wave = 0.3*np.sin(2*np.pi*freq*t)
        chunk = np.int16(wave*32767)
        audio = np.concatenate([audio, chunk])
    return audio

# --- 세션 상태로 A/B 멜로디 유지 ---
if 'melodies' not in st.session_state:
    st.session_state.melodies = [generate_melody(), generate_melody()]

melody_A, melody_B = st.session_state.melodies

# --- UI ---
st.title("🎵 Melody Preference Trainer")
st.write("키: C 기준 E3–E4 크로매틱, BPM=100, 4마디 멜로디를 선택하세요.")

st.subheader("Melody A")
audioA = melody_to_array(melody_A)
st.audio(audioA, sample_rate=SAMPLE_RATE)

st.subheader("Melody B")
audioB = melody_to_array(melody_B)
st.audio(audioB, sample_rate=SAMPLE_RATE)

st.markdown("---")

# --- 선택 저장 ---
def save(choice):
    ts = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO preferences (melody_a, melody_b, preferred, timestamp) VALUES (?, ?, ?, ?)",
        (str(melody_A), str(melody_B), choice, ts)
    )
    conn.commit()

st.subheader("Select Your Preference")
col1, col2 = st.columns(2)
with col1:
    if st.button("A 선택"):
        save('A')
        st.success("A 저장됨")
        st.session_state.melodies = [generate_melody(), generate_melody()]
        st.experimental_rerun()
with col2:
    if st.button("B 선택"):
        save('B')
        st.success("B 저장됨")
        st.session_state.melodies = [generate_melody(), generate_melody()]
        st.experimental_rerun()

st.markdown("---")

# --- Undo ---
if st.button("↩️ Undo Last"):
    c.execute("DELETE FROM preferences WHERE id=(SELECT MAX(id) FROM preferences)")
    conn.commit()
    st.success("마지막 삭제됨")
    st.experimental_rerun()

st.markdown("---")

# --- CSV 다운로드 ---
st.subheader("Download Data")
df = pd.read_sql_query("SELECT * FROM preferences", conn)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("⬇️ Download CSV", csv, "melody_preferences.csv", "text/csv")

st.markdown("---")

# --- 통계 ---
st.subheader("Statistics")
count = len(df)
st.write(f"총 선택 수: {count}")
if count:
    cnts = df['preferred'].value_counts().to_dict()
    st.write(f"A: {cnts.get('A',0)}회, B: {cnts.get('B',0)}회")
