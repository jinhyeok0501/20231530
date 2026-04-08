import streamlit as st
import google.generativeai as genai
import re
import time

# 1. 내 API 키를 기본값으로 설정
MY_API_KEY = "AIzaSyDJtKVtoo3hbDcOUSlTO91eVqa8Zfq0LpQ"

# 성격 튜닝 값에 따라 이모지 다르게 표시하기
def get_emoji(positivity, empathy):
    if positivity <= 50 and empathy <= 50:
        return "🧐"
    elif positivity > 50 and empathy <= 50:
        return "🤔"
    elif positivity <= 50 and empathy > 50:
        return "😥"
    else:
        return "🥰"

# 제목 설정하기
st.set_page_config(page_title="에코의 일기장", page_icon="📖", layout="centered")

# 세션 상태 초기화
if "diary_content" not in st.session_state:
    st.session_state.diary_content = ""
if "robot_response" not in st.session_state:
    st.session_state.robot_response = ""
if "emotion_color" not in st.session_state:
    st.session_state.emotion_color = "#F0F2F6" 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 사이드바 설정
with st.sidebar:
    st.title("⚙️ 설정")
    # value=MY_API_KEY를 추가하여 기본적으로 입력되어 있게 수정했습니다.
    api_key = st.text_input(
        "Gemini API 키 입력", 
        value=MY_API_KEY, 
        type="password", 
        help="Google Cloud에서 발급받은 Gemini API 키를 입력하세요."
    )

    st.subheader("🤖 로봇 성격 튜닝")
    positivity = st.slider("긍정 회로", 0, 100, 50, help="0=비관적/현실비판, 100=낙관적/희망회로")
    empathy = st.slider("공감 지수", 0, 100, 50, help="0=T(해결책/팩트), 100=F(공감/위로)")

    if api_key:
        genai.configure(api_key=api_key)
        st.success("에코가 연결되었습니다! ✅")
    else:
        st.warning("API 키를 입력해주세요.")
    

# 메인 화면
st.title("📖 마음을 읽는 일기 로봇, 에코")
st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{get_emoji(positivity, empathy)}</h1>", unsafe_allow_html=True)

st.subheader("오늘의 일기를 작성해주세요.")
# key를 diary_input으로 유지하되 value를 session_state와 연동
st.session_state.diary_content = st.text_area("일기장", height=200, value=st.session_state.diary_content, key="diary_input", placeholder="오늘 무슨 일이 있었나요?")

if st.button("[💌 일기 전달하기]", type="primary", use_container_width=True):
    if not api_key:
        st.error("API 키를 먼저 입력해주세요.")
    elif not st.session_state.diary_content:
        st.warning("일기 내용을 입력해주세요.")
    else:
        with st.spinner("에코가 일기를 읽고 감정을 분석 중입니다..."):
            system_instruction = f"""
            너는 사용자의 일기를 읽고 답장해주는 로봇 '에코'야.
            너의 현재 성격 설정: positivity({positivity}/100), empathy({empathy}/100).
            (positivity 낮음:현실비판/높음:희망회로, empathy 낮음:팩트/높음:공감위로)

            답변 형식: 반드시 아래 2가지 내용을 포함해서 자연스럽게 말해줘.
            1. 🎨 감정의 색깔: 이 일기의 감정을 대표하는 색상 이름과 Hex Code 하나만 작성 (예: 우울한 블루 #0000FF).
            2. 🤖 에코의 답장: 설정된 성격에 맞춰서, 일기 내용 중 구체적인 사건을 언급하며 친구처럼 다정하게 조언하거나 위로해줘.
            """

            # 모델 설정 (gemini-2.0-flash 권장 - 현재 사용 가능한 최신 안정 버전)
            # 사용
