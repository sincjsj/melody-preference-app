import streamlit as st
import numpy as np
import io
from scipy.io.wavfile import write as write_wav

st.title("🎵 Melody Preference Trainer")
st.write("UI가 정상적으로 뜨는지 확인하는 테스트입니다.")

# 1초짜리 440Hz (A) vs 660Hz (B) 사인파 생성
sr = 44100
t = np.linspace(0, 1, sr, endpoint=False)
audioA = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
audioB = (0.5 * np.sin(2 * np.pi * 660 * t)).astype(np.int16)

# 버퍼에 쓰기
bufA = io.BytesIO()
write_wav(bufA, sr, audioA)
bufA.seek(0)
bufB = io.BytesIO()
write_wav(bufB, sr, audioB)
bufB.seek(0)

# 오디오와 버튼
st.subheader("Melody A (440Hz)")
st.audio(bufA.read(), format="audio/wav")
if st.button("A 선택"):
    st.success("A를 선택하셨습니다!")

st.subheader("Melody B (660Hz)")
st.audio(bufB.read(), format="audio/wav")
if st.button("B 선택"):
    st.success("B를 선택하셨습니다!")
