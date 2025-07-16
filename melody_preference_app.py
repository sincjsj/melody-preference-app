# melody_preference_app.py

import streamlit as st
import numpy as np
import pandas as pd
from scipy.io.wavfile import write
import io
import tempfile
import os

# 기본 설정
BPM = 100
BEAT_DURATION = 60 / BPM  # 초 단위
STEPS = 32  # 4마디 = 32개 8분음표
SAMPLE_RATE = 44100
KEY_NOTES = [40, 42, 43, 45, 47, 48, 50, 52, 53, 55, 57, 59, 60]  # MIDI C Major + 범위 제한
PITCH_RANGE = (E3 := 52, E5 := 76)  # MIDI note number 기준

# 전역 로그 저장
if "log" not in st.session_state:
    st.session_state.log = []

def midi_to_freq(midi_note):
    return 440.0 * 2**((midi_note - 69) / 12)

def generate_melody():
    notes = np.random.choice(
        [n for n in KEY_NOTES if E3 <= n <= E5], size=STEPS
    )
    return notes.tolist()

def synthesize_melody(melody):
    total_duration = BEAT_DURATION * 0.5 * len(melody)  # 8분음표
    audio = np.zeros(int(SAMPLE_RATE * total_duration))
    t = np.linspace(0, BEAT_DURATION * 0.5, int(SAMPLE_RATE * BEAT_DURATION * 0.5), False)

    for i, midi in enumerate(melody):
        freq = midi_to_freq(midi)
        tone = 0.5 * np.sin(2 * np.pi * freq * t)
        start = int(i * len(t))
        audio[start:start+len(t)] += tone

    # Normalize
    audio = (audio * (2**15 - 1) / np.max(np.abs(audio))).astype(np.int16)
    return audio

def melody_to_wav_bytes(audio):
    buf = io.BytesIO()
    write(buf, SAMPLE_RATE, audio)
    return buf.getvalue()

def download_log(df):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Log as CSV", csv, file_name="melody_selection_log.csv", mime="text/csv")

# 인터페이스
st.title("🎼 Melody Preference App")
st.write("두 멜로디 중 더 선호하는 것을 선택해주세요.")

melody1 = generate_melody()
melody2 = generate_melody()

col1, col2 = st.columns(2)

with col1:
    st.audio(melody_to_wav_bytes(synthesize_melody(melody1)), format='audio/wav')
    if st.button("Melody A가 더 좋다"):
        st.session_state.log.append({"winner": "A", "melody_a": melody1, "melody_b": melody2})

with col2:
    st.audio(melody_to_wav_bytes(synthesize_melody(melody2)), format='audio/wav')
    if st.button("Melody B가 더 좋다"):
        st.session_state.log.append({"winner": "B", "melody_a": melody1, "melody_b": melody2})

if st.session_state.log:
    st.subheader("🔎 선택 로그")
    df = pd.DataFrame(st.session_state.log)
    st.dataframe(df)
    download_log(df)
