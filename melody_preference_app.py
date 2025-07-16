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

DURATION_TYPES = {
    1: 4.0,    # whole note = 4 beats
    2: 2.0,    # half note  = 2 beats
    4: 1.0,    # quarter    = 1 beat
    8: 0.5     # eighth     = 0.5 beat
}

# ——— 세션 상태 초기화 ———
if "log" not in st.session_state:
    st.session_state.log = []
if "melody1" not in st.session_state:
    st.session_state.melody1 = None
if "melody2" not in st.session_state:
    st.session_state.melody2 = None

# ——— 멜로디 생성 ———
def midi_to_freq(n):
    return 440.0 * 2**((n - 69) / 12)

def generate_melody():
    beats = 0.0
    melody = []
    while beats < 16.0:  # 4마디 × 4 beats = 16 beats
        dtype = random.choice(list(DURATION_TYPES.keys()))
        dur = DURATION_TYPES[dtype]
        # 남은 beats보다 크면 8분음표로 채움
        if beats + dur > 16.0:
            dur = DURATION_TYPES[8]
        note = random.choice([n for n in KEY_NOTES if PITCH_MIN <= n <= PITCH_MAX])
        melody.append((note, dur))
        beats += dur
    return melody

# ——— 음성 합성 ———
def synthesize(melody):
    segments = []
    for midi, dur in melody:
        secs = dur * BEAT_DURATION
        t = np.linspace(0, secs, int(SAMPLE_RATE * secs), False)
        tone = np.sin(2 * np.pi * midi_to_freq(midi) * t)
        segments.append(tone)
    audio = np.concatenate(segments)
    # Normalize 전체
    audio = (audio * (2**15 - 1) / np.max(np.abs(audio))).astype(np.int16)
    return audio

def wav_bytes(audio):
    buf = io.BytesIO()
    write(buf, SAMPLE_RATE, audio)
    return buf.getvalue()

# ——— 멜로디 초기 생성 ———
if st.session_state.melody1 is None or st.session_state.melody2 is None:
    st.session_state.melody1 = generate_melody()
    st.session_state.melody2 = generate_melody()

# ——— UI ———
st.title("🎶 Melody Preference App")
st.write(f"지금까지 선택한 횟수: **{len(st.session_state.log)}**")

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

# ——— 이전 선택 취소 ———
if st.session_state.log:
    if st.button("↩️ 이전 선택 취소", key="undo"):
        st.session_state.log.pop()

# ——— 로그 표시 & 다운로드 ———
if st.session_state.log:
    st.subheader("📝 선택 기록")
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 기록 다운로드 (CSV)",
        data=csv,
        file_name="melody_selection_log.csv",
        mime="text/csv"
    )
