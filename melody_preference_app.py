# melody_preference_app.py
# numpy+scipy 기반 사인파 생성, A/B 멜로디 선택, CSV 다운로드 및 Undo 기능 (샘플 기능 제거)

import streamlit as st
import random
import datetime
import sqlite3
import numpy as np
import io
import pandas as pd
from scipy.io.wavfile import write as write_wav

# --- 설정 ---
TEMPO = 100  # BPM
DURATION_DENOMS = [1, 2, 3, 4, 6, 8]  # 허용 박자 분모
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

# --- SQLite DB 초기화 ---
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

# --- 멜로디 생성 함수 (4마디) ---
def generate_melody():
    melody = []
    beats_left = TOTAL_BEATS
    while beats_left > 0:
        denom = random.choice(DURATION_DENOMS)
        beat = DURATION_BEATS[denom]
        if beat <= beats_left:
            note = random.choice(NOTE_NAMES)
            melody.append((note, denom))
            beats_left -= beat
    return melody

# --- 오디오 변환 함수 ---
@st.cache_data
def melody_to_wav_bytes(melody):
    audio = np.array([], dtype=np.int16)
    for note, denom in melody:
        duration_sec = (60 / TEMPO) * DURATION_BEATS[denom]
        t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
        freq = NOTE_FREQS[NOTE_NAMES.index(note)]
        wave = 0.3 * np.sin(2 * np.pi * freq * t)
        chunk = np.int16(wave * 32767)
        audio = np.concatenate((audio, chunk))
    buf = io.BytesIO()
    write_wav(buf, SAMPLE_RATE, audio)
    buf.seek(0)
    return buf.read()

# --- 세션 상태로 멜로디 유지 ---
if 'melodies' not in st.session_state:
    st.session_state.melodies = [generate_melody(), generate_melody()]

# --- UI 시작 ---
st.title('🎵 Melody Preference Trainer')
st.write('키: C 기준 E3–E4 크로매틱, BPM=100, 4마디 멜로디를 선택하세요.')

# --- 생성된 멜로디 재생 ---
st.subheader('Generated Melodies (4 bars)')
melody_A, melody_B = st.session_state.melodies
col1, col2 = st.columns(2)
with col1:
    st.markdown('**Melody A**')
    st.audio(melody_to_wav_bytes(melody_A), format='audio/wav')
with col2:
    st.markdown('**Melody B**')
    st.audio(melody_to_wav_bytes(melody_B), format='audio/wav')

st.markdown('---')

# --- 선호도 저장 ---
st.subheader('Select Your Preference')
def save_preference(choice):
    ts = datetime.datetime.now().isoformat()
    c.execute(
        'INSERT INTO preferences (melody_a, melody_b, preferred, timestamp) VALUES (?, ?, ?, ?)',
        (str(melody_A), str(melody_B), choice, ts)
    )
    conn.commit()

col3, col4 = st.columns(2)
with col3:
    if st.button('A 선택', key='select_A'):
        save_preference('A')
        st.success('선택 저장됨: A')
        st.session_state.melodies = [generate_melody(), generate_melody()]
        st.experimental_rerun()
with col4:
    if st.button('B 선택', key='select_B'):
        save_preference('B')
        st.success('선택 저장됨: B')
        st.session_state.melodies = [generate_melody(), generate_melody()]
        st.experimental_rerun()

st.markdown('---')

# --- 이전 선택 취소 ---
if st.button('↩️ Undo Last', key='undo'):
    c.execute('DELETE FROM preferences WHERE id = (SELECT MAX(id) FROM preferences)')
    conn.commit()
    st.success('마지막 선택이 삭제되었습니다.')
    st.experimental_rerun()

st.markdown('---')

# --- CSV 다운로드 ---
st.subheader('Download Data')
df = pd.read_sql_query('SELECT * FROM preferences', conn)
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button('⬇️ Download CSV', data=csv_data, file_name='melody_preferences.csv', mime='text/csv')

st.markdown('---')

# --- 통계 ---
st.subheader('Statistics')
count = df.shape[0]
st.write(f'총 선택 수: {count}')
if count > 0:
    counts = df['preferred'].value_counts().to_dict()
    st.write(f"A 선택: {counts.get('A', 0)}회, B 선택: {counts.get('B', 0)}회")
