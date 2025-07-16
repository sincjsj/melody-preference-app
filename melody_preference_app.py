import streamlit as st

st.title("🧪 Streamlit 스모크 테스트")
st.write("이 화면이 보이면 앱이 정상적으로 로드된 것입니다!")

if st.button("눌러보세요"):
    st.write("✅ 버튼이 작동합니다!")
