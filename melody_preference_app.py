# melody_preference_app.py

import streamlit as st
import numpy as np
import pandas as pd
import random
import io
from scipy.io.wavfile import write
import gspread
from google.oauth2 import service_account
import openai
st.write("✅ OPENAI_API_KEY:", st.secrets.get("OPENAI_API_KEY", "❌ 없음"))
# ——— 1) 설정 & 인증 ———
# OpenAI API 키
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Google Sheets API 인증
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

# Google 스프레드시트 ID로 열기
SPREADSHEET_ID = "1Tm8L1IqbYJ5jIZ03aQXYqpQ_y_WUPBVtTJCaOONDSck"
ws = gc.open_by_key(SPREADSHEET_ID).sheet1

# ——— 2) 로그 관리 함수 ———
def append_log(winner, m1, m2):
    ws.append_row([
        winner,
        str(m1),
        str(m2),
        pd.Timestamp.now(tz="Europe/London").strftime("%Y-%m-%d %H:%M:%S")
    ], value_input_option="USER_ENTERED")

def fetch_logs():
    return pd.DataFrame(ws.get_all_records())

# ——— 3) GPT 기반 멜로디 생성 ———
def generate_with_gpt(logs_df: pd.DataFrame):
    # 과거 선택 기록을 텍스트로 요약
history = "\n".join(
    f"{i+1}. {r['selected']} 선택: A{r['melody_a']} vs B{r['melody_b']}"
    for i, r in logs_df.iterrows()
)
    prompt = f"""
You are a melody-generation assistant.
User past choices:
{history}

Generate TWO new melodies in C key, 120 BPM, 4 bars (16 beats),
using durations 2,4,8 (half, quarter, eighth notes) only,
and pitches E3–E5.
Return JSON with keys "melody1" and "melody2", each a list of [midi, duration] pairs.
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate melodies."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    content = resp.choices[0].message.content.strip()
    # JSON 파싱
    data = pd.read_json(content)
    return data["melody1"].tolist(), data["melody2"].tolist()

# ——— 4) 랜덤 멜로디 생성 & 합성 ———
BPM = 120
BEAT_DURATION = 60 / BPM
SAMPLE_RATE = 44100
PITCH_MIN, PITCH_MAX = 52, 76           # E3–E5 (MIDI)
KEY_NOTES = list(range(PITCH_MIN, PITCH_MAX + 1))  # 크로매틱 스케일
DURATION_TYPES = {2: 2.0, 4: 1.0, 8: 0.5}          # half, quarter, eighth notes

def midi_to_freq(n: int) -> float:
    return 440.0 * 2**((n - 69) / 12)

def generate_random_melody():
    beats = 0.0
    melody = []
    while beats < 16.0:
        dtype = random.choice(list(DURATION_TYPES.keys()))
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

# ——— 5) 세션 초기화 ———
if "use_gpt" not in st.session_state:
    st.session_state.use_gpt = False
if "mel1" not in st.session_state or "mel2" not in st.session_state:
    # 최초 멜로디 생성
    logs_df = fetch_logs()
    st.session_state.mel1, st.session_state.mel2 = generate_with_gpt(logs_df)

# ——— 6) UI ———
st.title("🎶 Melody Preference with GPT & Google Sheets")
logs_df = fetch_logs()
st.write(f"총 선택 횟수: **{len(logs_df)}**")

# GPT 모드 토글
st.checkbox("GPT 기반 멜로디 사용", key="use_gpt")

# 멜로디 결정
if st.session_state.use_gpt:
    melody1, melody2 = st.session_state.mel1, st.session_state.mel2
else:
    melody1 = generate_random_melody()
    melody2 = generate_random_melody()

col1, col2 = st.columns(2)
with col1:
    st.audio(wav_bytes(synthesize(melody1)), format="audio/wav")
    if st.button("🎵 A 선택", key="A"):
        append_log("A", melody1, melody2)
        st.experimental_rerun()

with col2:
    st.audio(wav_bytes(synthesize(melody2)), format="audio/wav")
    if st.button("🎵 B 선택", key="B"):
        append_log("B", melody1, melody2)
        st.experimental_rerun()

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
