# melody_preference_app.py

import streamlit as st
import numpy as np
import pandas as pd
import random
import io
from scipy.io.wavfile import write
import gspread
from google.oauth2 import service_account

# ——— 1) Google Sheets 연동 설정 ———
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)
ws = gc.open("MelodyLog").sheet1   # Google 스프레드시트 이름

def append_log(winner, m1, m2):
    """선택 결과를 시트에 한 행으로 추가"""
    ws.append_row([
        winner,
        str(m1),
        str(m2),
        pd.Timestamp.now(tz="Europe/London").strftime("%Y-%m-%d %H:%M:%S")
    ], value_input_option="USER_ENTERED")

def fetch_logs():
    """시트 전체 기록을 DataFrame으로 반환"""
    return pd.DataFrame(ws.get_all_records())

# ——— 2) 멜로디 생성·합성 설정 ———
BPM = 120
BEAT_DURATION = 60 / BPM
SAMPLE_RATE = 44100
PITCH_MIN, PITCH_MAX = 52, 76         # E3–E5 (MIDI)
KEY_NOTES = list(range(PITCH_MIN, PITCH_MAX + 1))  # 크로매틱
DURATION_TYPES = {2: 2.0, 4: 1.0, 8: 0.5}          # half, quarter, eighth

def midi_to_freq(n):
    return 440.0 * 2**((n - 69) / 12)

def generate_melody():
    beats = 0.0
    melody = []
    while beats < 16.0:             # 4마디 × 4박자 = 16박자
        dtype = random.choice(list(DURATION_TYPES))
        dur = DURATION_TYPES[dtype]
        if beats + dur > 16.0:
            dur = DURATION_TYPES[8]
        note = random.choice(KEY_NOTES)
        melody.append((note, dur))
        beats += dur
    return melody

def synthesize(melody):
    parts = []
    for midi, dur in melody:
        secs = dur * BEAT_DURATION
        t = np.linspace(0, secs, int(SAMPLE_RATE * secs), False)
        parts.append(np.sin(2 * np.pi * midi_to_freq(midi) * t))
    audio = np.concatenate(parts)
    return (audio * (2**15 - 1) / np.max(np.abs(audio))).astype(np.int16)

def wav_bytes(audio):
    buf = io.BytesIO()
    write(buf, SAMPLE_RATE, audio)
    return buf.getvalue()

# ——— 3) 세션에 현재 멜로디 저장 ———
if "melody1" not in st.session_state:
    st.session_state.melody1 = generate_melody()
    st.session_state.melody2 = generate_melody()

# ——— 4) UI ———
st.title("🎶 Melody Preference App (Google Sheets)")
logs_df = fetch_logs()
st.write(f"총 선택 횟수: **{len(logs_df)}**")

col1, col2 = st.columns(2)
with col1:
    st.audio(wav_bytes(synthesize(st.session_state.melody1)), format="audio/wav")
    if st.button("🎵 Melody A 선택", key="A"):
        append_log("A", st.session_state.melody1, st.session_state.melody2)
        st.session_state.melody1 = generate_melody()
        st.session_state.melody2 = generate_melody()

with col2:
    st.audio(wav_bytes(synthesize(st.session_state.melody2)), format="audio/wav")
    if st.button("🎵 Melody B 선택", key="B"):
        append_log("B", st.session_state.melody1, st.session_state.melody2)
        st.session_state.melody1 = generate_melody()
        st.session_state.melody2 = generate_melody()

st.markdown("---")
st.subheader("📝 전체 선택 기록")
st.dataframe(logs_df, use_container_width=True)

csv = logs_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 전체 기록 다운로드 (CSV)",
    data=csv,
    file_name="melody_log.csv",
    mime="text/csv"
)
