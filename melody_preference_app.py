import streamlit as st
import numpy as np

st.title("🔊 오디오 재생 테스트")
st.write("아래 플레이어에서 440 Hz 톤을 재생해 보세요.")

# 1초짜리 440Hz 사인파 생성
sr = 44100
t = np.linspace(0, 1, sr, endpoint=False)
tone = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

# st.audio에 numpy array와 sample_rate 직접 전달
st.audio(tone, sample_rate=sr)
