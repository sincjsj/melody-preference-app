import streamlit as st
import numpy as np
import io
from scipy.io.wavfile import write as write_wav

st.title("🎵 Melody Preference Trainer")
st.write("이제 A와 B 사인파가 뜨고, 버튼도 보일 겁니다.")

# 1초짜리 440Hz vs 660Hz
sr = 44100
t = np.linspace(0, 1, sr, endpoint=False)
audioA = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
audioB = (0.5 * np.sin(2 * np.pi * 660 * t)).astype(np.int16)

# 메모리 버퍼에 WAV로 쓰기
bufA = io.BytesIO()
write_wav(bufA, sr, audioA)
bufA.seek(0)
bufB = io.BytesIO()
write_wav(bufB, sr, audioB)
bufB.seek(0)

st.subheader("Melody A (440Hz)")
st.audio(bufA.read(), format="audio/wav")

st.subheader("Melody B (660Hz)")
st.audio(bufB.read(), format="audio/wav")

col1, col2 = st.columns(2)
with col1:
    if st.button("A 선택"):
        st.success("✅ A 선택됨")
with col2:
    if st.button("B 선택"):
        st.success("✅ B 선택됨")
