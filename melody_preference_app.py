# melody_preference_app.py
# numpy+scipy 기반 사인파 음원 생성으로 pydub 제거한 버전

import streamlit as st
import random
import datetime
import sqlite3
import os
import uuid
import numpy as np
import io
from scipy.io.wavfile import write as write_wav

# 설정
TEMPO = 120  # BPM
QUARTER_BEATS = 4  # 4분음표를 1로 볼 때 기준
DURATION_BEATS = {1: 4, 2: 2, 4: 1, 8: 0.5, 16: 0.25}
SAMPLE_RATE = 44100  # Hz

# 음높이 데이터: C3(130.81Hz) ~ B5(987.77Hz)
OCTAVE_NOTES = [
    ('C3', 130.81), ('D3', 146.83), ('E3', 164.81), ('F3', 174.61), ('G3', 196.00), ('A3', 220.00), ('B3', 246.94),
    ('C4', 261.63), ('D4', 293.66), ('E4', 329.63), ('F4', 349.23), ('G4', 392.00), ('A4', 440.00), ('B4', 493.88),
    ('C5', 523.25), ('D5', 587.33), ('E5', 659.25), ('F5', 698.46), ('G5', 783.99), ('A5', 880.00), ('B5', 987.77)
]
NOTE_NAMES, NOTE_FREQS = zip(*OCTAVE_NOTES)

# SQLite DB 초기화
DB_PATH = 'melody_preferences.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute(
    '''CREATE TABLE IF NOT EXISTS preferences (
           id INTEGER PRIMARY KEY,
           melody_a TEXT,
           melody_b TEXT,
           preferred TEXT,
           timestamp TEXT
       )'''
)
conn.commit()

# 8마디 랜덤 멜로디 생성 (4/4 박자 총 32박자)
def generate_melody():
    melody = []
    beats_left = 32
    while beats_left > 0:
        denom = random.choice(list(DURATION_BEATS.keys()))
        beat = DURATION_BEATS[denom]
        if beat <= beats_left:
            note = random.choice(NOTE_NAMES)
            melody.append((note, denom))
            beats_left -= beat
    return melody

# 멜로디를 WAV 바이트로 변환
def melody_to_wav_bytes(melody):
    audio = np.array([], dtype=np.int16)
    for note, denom in melody:
        freq = NOTE_FREQS[NOTE_NAMES.index(note)]
        duration_sec = (60 / TEMPO) * DURATION_BEATS[denom]
        t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
        wave = 0.3 * np.sin(2 * np.pi * freq * t)
        # 16-bit PCM 변환
        chunk = np.int16(wave * 32767)
        audio = np.concatenate((audio, chunk))
    # WAV 파일을 메모리로 쓰기
    buffer = io.BytesIO()
    write_wav(buffer, SAMPLE_RATE, audio)
    buffer.seek(0)
    return buffer.read()

# Streamlit UI
st.title('🎵 Melody Preference Trainer')
st.write('두 멜로디를 듣고 더 좋은 것을 선택하세요. 선택 데이터는 DB에 저장됩니다.')

# 멜로디 생성 및 오디오 생성
melody_A = generate_melody()
melody_B = generate_melody()

wav_A = melody_to_wav_bytes(melody_A)
wav_B = melody_to_wav_bytes(melody_B)

col1, col2 = st.columns(2)
with col1:
    st.subheader('Melody A')
    st.audio(wav_A, format='audio/wav')
with col2:
    st.subheader('Melody B')
    st.audio(wav_B, format='audio/wav')

# 선택 저장 함수
def save_preference(choice):
    timestamp = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO preferences (melody_a, melody_b, preferred, timestamp) VALUES (?, ?, ?, ?)",
        (str(melody_A), str(melody_B), choice, timestamp)
    )
    conn.commit()
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

# 저장된 선택 수 표시
c.execute('SELECT COUNT(*) FROM preferences')
count = c.fetchone()[0]
st.markdown('---')
st.write(f'총 선택 수: {count}')
