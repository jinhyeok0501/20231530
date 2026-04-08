import streamlit as st
import google.generativeai as genai
import re
import time # 피드백 후 잠시 대기를 위해 추가

MY_API_KEY = "AIzaSyDJtKVtoo3hbDcOUSlTO91eVqa8Zfq0LpQ"

# 성격 튜닝 값에 따라 이모지 다르게 표시하기
def get_emoji(positivity, empathy):
    if positivity <= 50 and empathy <= 50:
        return "🧐"  # T + 부정 = 사려 깊음 / 분석적
    elif positivity > 50 and empathy <= 50:
        return "🤔"  # T + 긍정 = 낙관적 / 분석적
    elif positivity <= 50 and empathy > 50:
        return "😥"  # F + 부정 = 슬픔 / 공감
    else:
        return "🥰"  # F + 긍정 = 사랑스러움 / 공감

# 제목 설정하기
st.set_page_config(page_title="에코의 일기장", page_icon="📖", layout="centered")

# 세션의 상태를 초기화하기
if "diary_content" not in st.session_state:
    st.session_state.diary_content = ""
if "robot_response" not in st.session_state:
    st.session_state.robot_response = ""
if "emotion_color" not in st.session_state:
    # 기본 색상 회색으로 설정하기
    st.session_state.emotion_color = "#F0F2F6" 
# 대화 히스토리 저장을 위한 세션을 ㅇ추가하기
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# 사이드바 설정
with st.sidebar:
    # gemini api키 입력하는 칸 만들기 (교사의 api 복사해서 입력)
    st.title("⚙️ 설정")
    api_key = st.text_input("Gemini API 키 입력", value=MY_API_KEY, type="password", help="Google Cloud에서 발급받은 Gemini API 키를 입력하세요.")

    # 로봇 성격을 튜닝하는 slider
    st.subheader("🤖 로봇 성격 튜닝")
    positivity = st.slider("긍정 회로", 0, 100, 50, help="0=비관적/현실비판, 100=낙관적/희망회로")
    empathy = st.slider("공감 지수", 0, 100, 50, help="0=T(해결책/팩트), 100=F(공감/위로)")

    # api 키 입력 확인 문구 표시
    if api_key:
        genai.configure(api_key=api_key)
        st.success("API 키가 설정되었습니다!")
    else:
        st.warning("API 키를 입력해주세요.")
    

# 메인 화면 (제목 표시)
st.title("📖 마음을 읽는 일기 로봇, 에코")

# 사이드바 설정 상태에 따라 에코 이모지 다르게 표시하기
st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{get_emoji(positivity, empathy)}</h1>", unsafe_allow_html=True)

# 일기 작성할 수 있는 칸
st.subheader("오늘의 일기를 작성해주세요.")
st.session_state.diary_content = st.text_area("일기장", height=200, value=st.session_state.diary_content, key="diary_input", placeholder="오늘 무슨 일이 있었나요?")

# 일기 작성하기 
if st.button("[💌 일기 전달하기]", type="primary", use_container_width=True):
    # api 키 없이 작성했을 때 표시
    if not api_key:
        st.error("API 키를 먼저 입력해주세요.")
    # 내용 없이 작성했을 때 표시
    elif not st.session_state.diary_content:
        st.warning("일기 내용을 입력해주세요.")
    # api와 내용 모두 작성 후 버튼을 눌렀을 때 분석 시작
    else:
        with st.spinner("에코가 일기를 읽고 감정을 분석 중입니다..."):
            # gemini 일기 내용 분석 및 답변 프롬프트
            system_instruction = f"""
            너는 사용자의 일기를 읽고 답장해주는 로봇 '에코'야.
            # 사이드바 설정 따라서 성격 설정
            너의 현재 성격 설정: positivity({positivity}/100), empathy({empathy}/100).
            (positivity 낮음:현실비판/높음:희망회로, empathy 낮음:팩트/높음:공감위로)

            # 답변 형식 지정
            답변 형식: 반드시 아래 2가지 내용을 포함해서 자연스럽게 말해줘.
            1. 🎨 감정의 색깔: 이 일기의 감정을 대표하는 색상 이름과 Hex Code 하나만 작성 (예: 우울한 블루 #0000FF).
            2. 🤖 에코의 답장: 설정된 성격에 맞춰서, 일기 내용 중 구체적인 사건을 언급하며 친구처럼 다정하게 조언하거나 위로해줘.
            """

            # 모델 설정 (gemini-2.5-flash)
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            
            # 기존 히스토리를 불러와서 대화 시작 (피드백 반영하기 위함)
            chat = model.start_chat(history=st.session_state.chat_history)
            
            full_prompt = system_instruction + "\n\n[오늘의 일기]:\n" + st.session_state.diary_content
            
            response = chat.send_message(full_prompt)
            st.session_state.robot_response = response.text
            
            # 업데이트된 히스토리를 다시 저장하기기
            st.session_state.chat_history = chat.history

            # 색상 추출하기 (감정에 맞게)
            try:
                color_match = re.search(r'#(?:[0-9a-fA-F]{3}){1,2}', st.session_state.robot_response)
                if color_match:
                    st.session_state.emotion_color = color_match.group(0)
                else:
                    st.session_state.emotion_color = "#F0F2F6" # 기본 색상
            except Exception as e:
                st.session_state.emotion_color = "#F0F2F6"

            st.rerun()

# 결과 화면 표시 & 피드백 남길 수 있도록 하기
if st.session_state.robot_response:
    st.write("---")
    st.subheader("🎨 에코의 감정 분석 결과")
    
    # 감정을 표현한 색깔로 표현한 박스 안에 답변 표시하기
    st.markdown(f"""
    <div style='background-color:{st.session_state.emotion_color}; 
                padding: 40px; 
                border-radius: 20px; 
                margin-bottom: 20px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                border: 2px solid #ffffff;'>
        <div style='background-color: rgba(255, 255, 255, 0.8); padding: 20px; border-radius: 15px;'>
            {st.session_state.robot_response.replace('\n', '<br>')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 감정 분석이나 일기 답변이 의도와 다를 때, 피드백 남기기 (진짜 감정과 바라는 점 2개 항목)
    with st.expander("🛠️ 에코 더 똑똑하게 만들기 (피드백 전송)"):
        st.write("로봇의 분석이 아쉬웠나요? 솔직한 감정을 알려주시면 다음 분석에 반영됩니다.")
        feedback_emotion = st.text_input("내가 느낀 진짜 감정은?", placeholder="예: 슬픔보다는 억울함에 가까워.")
        feedback_wish = st.text_area("로봇에게 바라는 점", placeholder="예: 해결책보다는 그냥 내 편을 들어줘.")

        # 피드백 작성 후 누르는 전송 버튼
        if st.button("[피드백 전송 및 기억시키기]"):
            if feedback_emotion or feedback_wish:
                # 피드백 내용을 대화 기록 형식으로 만들기
                feedback_prompt = f"""
                [SYSTEM NOTE: 사용자가 이전 분석에 대해 피드백을 주었습니다.]
                - 사용자의 실제 감정: {feedback_emotion}
                - 사용자의 요구사항: {feedback_wish}
                (다음 일기 분석 시 이 피드백을 최우선으로 고려하여 성격과 답변 방향을 조정하세요.)
                """
                
                # 히스토리에 유저 메시지로 추가
                st.session_state.chat_history.append({"role": "user", "parts": [feedback_prompt]})
                # 모델이 답변한 것처럼 더미 응답 추가하기 (히스토리 짝을 맞추기 위해서)
                st.session_state.chat_history.append({"role": "model", "parts": ["알겠습니다. 입력해주신 피드백을 메모리에 저장했습니다. 다음 분석부터 반영하겠습니다."]})
                
                st.success("피드백이 에코의 장기 기억장치에 저장되었습니다! 🧠")
                time.sleep(2) # 학생이 메시지를 볼 시간을 주기
                st.rerun() # 화면 새로고침하여 상태 업데이트
            else:
                st.warning("피드백 내용을 입력해주세요.")
