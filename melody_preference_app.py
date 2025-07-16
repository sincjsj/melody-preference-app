# melody_preference_app.py
# 8마디 두 멜로디를 생성해 소리로 들려주고, 사용자 선택을 SQLite DB에 저장

import streamlit as st
import random
import datetime
import sqlite3
import os
import uuid
from pydub.generators import Sine
from pydub import AudioSegment
import base64

# 전체 설정
TEMPO = 120  # BPM
QUARTER_MS = int(60_000 / TEMPO)  # 1분음표(quarter note) ms
DURATION_BEATS = {1: 4, 2: 2, 4: 1, 8: 0.5, 16: 0.25}
DURATION_MS = {denom: int(QUARTER_MS * beats) for denom, beats in DURATION_BEATS.items()}

# 음역대: C3(130.81Hz) ~ B5(987.77Hz) 약 3옥타브
OCTAVE_NOTES = [
    ('C3', 130.81), ('D3', 146.83), ('E3', 164.81), ('F3', 174.61), ('G3', 196.00), ('A3', 220.00), ('B3', 246.94),
    ('C4', 261.63), ('D4', 293.66), ('E4', 329.63), ('F4', 349.23), ('G4', 392.00), ('A4', 440.00), ('B4', 493.88),
    ('C5', 523.25), ('D5', 587.33), ('E5', 659.25), ('F5', 698.46), ('G5', 783.99), ('A5', 880.00), ('B5', 987.77)
]
NOTE_NAMES, NOTE_FREQS = zip(*OCTAVE_NOTES)

# DB 초기화
DB_PATH = 'melody_preferences.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute(
    '''CREATE TABLE IF NOT EXISTS preferences (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           melody_a TEXT,
           melody_b TEXT,
           preferred TEXT,
           timestamp TEXT
       )'''
)
conn.commit()

# 랜덤 멜로디 생성 (8마디, 4/4박자 기준 총 32비트)
def generate_melody():
    melody = []
    total_beats = 32
    while total_beats > 0:
        denom = random.choice(list(DURATION_BEATS.keys()))
        beats = DURATION_BEATS[denom]
        if beats <= total_beats:
            pitch = random.choice(NOTE_NAMES)
            melody.append((pitch, denom))
            total_beats -= beats
    return melody

# 멜로디를 오디오(mp3)로 변환
def melody_to_audio(melody, filename):
    audio = AudioSegment.silent(duration=0)
    for note, denom in melody:
        freq = NOTE_FREQS[NOTE_NAMES.index(note)]
        tone = Sine(freq).to_audio_segment(duration=DURATION_MS[denom]).apply_gain(-3)
        audio += tone
    audio.export(filename, format='mp3')

# 오디오 플레이어 HTML
def get_audio_html(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<audio controls src="data:audio/mp3;base64,{b64}"></audio>'

# Streamlit UI
st.title('🎵 Melody Preference Trainer')
st.write('두 멜로디를 듣고 더 좋은 멜로디를 선택하세요. 선택 데이터는 DB에 저장됩니다.')

# 멜로디 생성 및 파일 준비
melody_A = generate_melody()
melody_B = generate_melody()
file_A = f'melody_A_{uuid.uuid4().hex}.mp3'
file_B = f'melody_B_{uuid.uuid4().hex}.mp3'
melody_to_audio(melody_A, file_A)
melody_to_audio(melody_B, file_B)

col1, col2 = st.columns(2)
with col1:
    st.markdown('**Melody A**')
    st.markdown(get_audio_html(file_A), unsafe_allow_html=True)
with col2:
    st.markdown('**Melody B**')
    st.markdown(get_audio_html(file_B), unsafe_allow_html=True)

# 선택 저장 함수
def save_preference(choice):
    timestamp = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO preferences (melody_a, melody_b, preferred, timestamp) VALUES (?, ?, ?, ?)",
        (str(melody_A), str(melody_B), choice, timestamp)
    )
    conn.commit()
    # 임시 파일 삭제
    for f in [file_A, file_B]:
        try:
            os.remove(f)
        except:
            pass
    st.success(f'선택 저장됨: {choice}')
    st.experimental_rerun()

# 버튼
col3, col4 = st.columns(2)
with col3:
    if st.button('A 선택'):
        save_preference('A')
with col4:
    if st.button('B 선택'):
        save_preference('B')

# 기록 수 표시
c.execute('SELECT COUNT(*) FROM preferences')
count = c.fetchone()[0]
st.markdown('---')
st.write(f'총 선택 수: {count}')
