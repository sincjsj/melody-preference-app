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

# ——— 1) 설정 & 인증 ———

openai.api_key = st.secrets["OPENAI_API_KEY"]

creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(creds)

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
        f"{i+1}. {r['winner']} 선택: A{r['melody_a']} vs B{r['melody_b']}"
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
    data = pd.read_json(content)
    return data["melody1"].tolist(), data["melody2"].tolist()

# ——— 4) 랜덤 멜로디 생성 & 합성 ———

BPM = 120
BEAT = 60 / BPM
SR = 44100
KEY_NOTES = list(range(52, 77))             # E3–E5
DUR = {2: 2.0, 4: 1.0, 8: 0.5}

def midi_to_freq(n):
    return 440.0 * 2**((n - 69) / 12)

def generate_random_melody():
    beats = 0.0
    mel = []
    while beats < 16.0:
        d = random.choice(list(DUR.keys()))
        dur = DUR[d]
        if beats + dur > 16.0:
            dur = DUR[8]
        note = random.choice(KEY_NOTES)
        mel.append((note, dur))
        beats += dur
    return mel

def synthesize(mel):
    parts = []
    for n, d in mel:
        secs = d * BEAT
        t = np.linspace(0, secs, int(SR * secs), False)
        parts.append(np.sin(2 * np.pi * midi_to_freq(n) * t))
    audio = np.concatenate(parts)
    return (audio * (2**15 - 1) / np.max(np.abs(audio))).astype(np.int16)

def wav_bytes(audio):
    buf = io.BytesIO()
    write(buf, SR, audio)
    return buf.getvalue()

# ——— 5) 세션 초기화 ———

if "use_gpt" not in st.session_state:
    st.session_state.use_gpt = False

if "mel1" not in st.session_state or "mel2" not in st.session_state:
    logs = fetch_logs()
    st.session_state.mel1, st.session_state.mel2 = generate_with_gpt(logs)

# ——— 6) UI ———

st.title("🎶 Melody Preference with GPT & Google Sheets")
logs_df = fetch_logs()
st.write(f"총 선택 횟수: **{len(logs_df)}**")

st.checkbox("GPT 기반 멜로디 사용", key="use_gpt")

if st.session_state.use_gpt:
    m1, m2 = st.session_state.mel1, st.session_state.mel2
else:
    m1, m2 = generate_random_melody(), generate_random_melody()

col1, col2 = st.columns(2)
with col1:
    st.audio(wav_bytes(synthesize(m1)), format="audio/wav")
    if st.button("🎵 A 선택"):
        append_log("A", m1, m2)
        st.experimental_rerun()

with col2:
    st.audio(wav_bytes(synthesize(m2)), format="audio/wav")
    if st.button("🎵 B 선택"):
        append_log("B", m1, m2)
        st.experimental_rerun()

st.markdown("---")
st.subheader("📝 전체 선택 기록")
st.dataframe(logs_df, use_container_width=True)

csv = logs_df.to_csv(index=False).encode()
st.download_button("📥 기록 다운로드 (CSV)", csv, "melody_log.csv", "text/csv")
