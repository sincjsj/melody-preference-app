# melody_preference_app.py

import streamlit as st
import numpy as np
import pandas as pd
import random
from scipy.io.wavfile import write
import io

# ——— 설정 ———
BPM = 100
BEAT_DURATION = 60 / BPM           # 1 beat (quarter note) 길이 (초)
SAMPLE_RATE = 44100
KEY_NOTES = [60, 62, 64, 65, 67, 69, 71]  # C Major scale (MIDI)
PITCH_MIN, PITCH_MAX = 52, 76     # E3–E5 (MIDI)

# 2, 4, 8분음표만 사용
DURATION_TYPES = {
    2: 2.0,    # half note  = 2 beats
    4: 1.0,    # quarter    = 1 beat
    8: 0.5     # eighth     = 0.5 beat
}

# ——— 세션 상태 초기화 ———
if "log" not in st.session_state:
    st.session_state.log = []
if "melody1" not in st.session_state or "melody2" not in st.session_state:
    st.session_state.melody1 = None
    st.session_state.melody2 = None

# ——— 멜로디 생성 함수 ———
def midi_to_freq(n):
    return 440.0 * 2**((n - 69) / 12)

def generate_melody():
    beats = 0.0
    melody = []
    while beats < 16.0:  # 4마디 × 4 beats = 16 beats
        dtype = random.choice(list(DURATION_TYPES.keys()))
        dur = DURATION_TYPES[dtype]
        if beats + dur > 16.0:
            dur = DURATION_TYPES[8]
        note = random.choice([n for n in KEY_NOTES if PITCH_MIN <= n <= PITCH_MAX])
        melody.append((note, dur))
        beats += dur
    return melody

# ——— 합성 및 WAV 변환 ———
def synthesize(melody):
    segments = []
    for midi, dur in melody:
        secs = dur * BEAT_DURATION
        t = np.linspace(0, secs, int(SAMPLE_RATE * secs), False)
        tone = np.sin(2 * np.pi * midi_to_freq(midi) * t)
        segments.append(tone)
    audio = np.concatenate(segments)
    audio = (audio * (2**15 - 1) / np.max(np.abs(audio))).astype(np.int16)
    return audio

def wav_bytes(audio):
    buf = io.BytesIO()
    write(buf, SAMPLE_RATE, audio)
    return buf.getvalue()

# ——— 첫 멜로디 생성 ———
if st.session_state.melody1 is None or st.session_state.melody2 is None:
    st.session_state.melody1 = generate_melody()
    st.session_state.melody2 = generate_melody()

# ——— UI ———
st.title("🎶 Melody Preference App")
st.write(f"지금까지 선택한 횟수: **{len(st.session_state.log)}**")

# 두 멜로디 동시 재생 및 선택
col1, col2 = st.columns(2)
with col1:
    st.audio(wav_bytes(synthesize(st.session_state.melody1)), format="audio/wav")
    if st.button("🎵 Melody A 선택", key="choose_A"):
        st.session_state.log.append({
            "winner": "A",
            "melody_a": st.session_state.melody1,
            "melody_b": st.session_state.melody2
        })
        st.session_state.melody1 = generate_melody()
        st.session_state.melody2 = generate_melody()

with col2:
    st.audio(wav_bytes(synthesize(st.session_state.melody2)), format="audio/wav")
    if st.button("🎵 Melody B 선택", key="choose_B"):
        st.session_state.log.append({
            "winner": "B",
            "melody_a": st.session_state.melody1,
            "melody_b": st.session_state.melody2
        })
        st.session_state.melody1 = generate_melody()
        st.session_state.melody2 = generate_melody()

st.markdown("---")

# Undo 버튼 (항상 표시)
if st.button("↩️ 이전 선택 취소"):
    if st.session_state.log:
        st.session_state.log.pop()
    else:
        st.warning("취소할 선택이 없습니다.")

# 로그 테이블 (선택이 있을 때만)
if st.session_state.log:
    st.subheader("📝 선택 기록")
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df, use_container_width=True)
else:
    df = pd.DataFrame(columns=["winner", "melody_a", "melody_b"])

# 다운로드 버튼 (항상 표시)
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 기록 다운로드 (CSV)",
    data=csv,
    file_name="melody_selection_log.csv",
    mime="text/csv"
)
