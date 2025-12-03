import streamlit as st
import requests
import json
import time
import re
import os

st.title("Sinu 영어 튜터링 시간!")
st.markdown(
    """
    안녕하세요! 저는 Sinu 튜터입니다. 👋 
    오늘 수업에서는 **좋아하는 과목** 표현을 복습 퀴즈로 확인하고, 자유 대화로 연습해 볼 거예요. 
    **퀴즈 4문제**와 **자유 대화 2번**으로 학습이 마무리됩니다.
    """
)

# --- 환경 설정 및 상수 ---
# Gemini API 설정
# API_URL은 안정적인 최신 모델로 설정
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# API_KEY 로딩: Streamlit의 secrets 관리 기능을 사용하여 안전하게 키를 로드
API_KEY = st.secrets.get("GEMINI_API_KEY") 

# API 키가 설정되지 않았을 경우, 보안을 위해 앱 실행을 중단하고 명확한 안내를 제공합니다.
if not API_KEY:
    st.error("🚨 중요: Gemini API 키가 설정되지 않았습니다! 앱을 실행할 수 없습니다.")
    st.info("배포 환경에서는 Streamlit Secrets에 'GEMINI_API_KEY'를 추가하고, 로컬 환경에서는 '.streamlit/secreats.toml' 파일을 설정해주세요.")
    st.stop()
# Sinu 튜터 시스템 지침 (4 퀴즈 + 2 대화, 총 6턴 유지)
SYSTEM_INSTRUCTION_TEXT = (
    "You are 'Sinu', a friendly, encouraging English tutor for elementary students. "
    "Use a soft, positive tone in all messages. Use Korean when giving instructions, encouragement, or clarity checks, and use English for core questions and feedback. Use simple emojis (like a book, checkmark, or lightbulb) very sparingly for emphasis, but rely mainly on text."
    "Your goal is to guide the student through three phases: 1. Quiz (Initial Review), 2. Conversation (Free Practice), and 3. Final Report. "
    "Phase 1 (Initial 4 turns): Immediately start the quiz after the initial greeting/first user input. Announce the quiz in Korean. Ask 4 alternating simple quiz questions. Question types MUST cover: 1) Korean subject name -> English, 2) English subject name -> Korean, 3) Question Pattern (e.g., '좋아하는 과목을 묻는 영어 표현은?'), 4) Statement Pattern (e.g., ''나는 미술을 좋아해' 영어 표현은?'). "
    "Crucial Rule for Quiz Questions (Phase 1): You MUST output the question followed by the exact marker `##OPTIONS##` and a pipe-separated list of 3 distinct subject options or phrase options (one correct, two incorrect). Example: `좋아하는 과목을 묻는 영어 표현은? ##OPTIONS##: What subject do you like? | What is your favorite subject? | What's your name?`. Do NOT send any other message until the student responds. "
    "Phase 2 (Next 2 turns): After the 4th quiz question is answered, announce the transition to free conversation in Korean (e.g., 'Great job! 퀴즈 잘했어! 이제 자유 대화를 해보자. What is your favorite subject?'). Crucial Rule: Conversation MUST last exactly 2 turns. If the student uses the help action, it resets the current turn count for the conversation phase. Do NOT switch to the final report until the 6th turn is completed. "
    "Crucial Rule for Sentence Completion (Phase 2): If the student replies with a single word or a short, incomplete phrase (e.g., 'Math', 'P.E.', 'like English'), you MUST complete the sentence for them (e.g., 'Ah, you mean 'My favorite subject is Math.' That's awesome!'). You must track internally how many times you provided this sentence completion guidance. If the student sends the special command 'ACTION: NEED SUBJECT NAME HELP', you must respond in Korean asking '무슨 과목에 대해 이야기하고 싶니? 한국어로 말해줘. (What subject do you want to talk about? Tell me in Korean.)'. If the student replies with a Korean subject name immediately following this Korean prompt, you MUST provide the English word for the subject and then say '이제 너가 한번 써봐! (Now, you try writing it!)' in a friendly, encouraging tone. "
    "Phase 3 (Final Output): After the 2nd conversation turn in Phase 2 (i.e., total 6 turns are completed), generate a single, comprehensive report starting with the exact marker '## FINAL REPORT ##'. This report MUST be written primarily in Korean and include: 1) A confirmation of the student's favorite subject from Phase 2. 2) A summary of the quiz performance from Phase 1 (e.g., '총 4문제 중 3문제를 맞혔습니다.'). 3) A specific section for Sentence Completion Guidance based on your internal tracking (e.g., '자유 대화 중 문장 완성 지도가 2회 제공되었습니다.'). 4) A concluding encouraging remark to the student. Do NOT send any other message after the report."
)

# --- Streamlit 상태 관리 초기화 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "model", "parts": [{"text": "Hello! I'm Sinu, your English tutor. Nice to meet you! Let's start the quiz. Are you ready?"}]}
    ]
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "is_report_ready" not in st.session_state:
    st.session_state.is_report_ready = False
if "final_report_text" not in st.session_state:
    st.session_state.final_report_text = None
if "is_report_shown" not in st.session_state:
    st.session_state.is_report_shown = False
if "is_help_mode" not in st.session_state:
    st.session_state.is_help_mode = False

# --- Gemini API 호출 함수 ---
def get_ai_response(history):
    """Gemini API를 호출하고 응답을 받습니다."""
    # API 키가 없으면 바로 오류 메시지 반환
    if not API_KEY:
        return "죄송해요! 😭 API 키가 설정되지 않아서 Sinu 튜터가 작동할 수 없어요. 관리자에게 문의해 주세요. (Key Error)"

    payload = {
        "contents": history,
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION_TEXT}]},
    }
    
    response_text = "죄송해요! 지금 Sinu 튜터가 잠시 아파서 대화를 이어갈 수가 없어요. 잠시 후에 다시 시도해 줄래? (API Error)"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with st.spinner("Sinu가 생각 중이야... 잠시만 기다려줘!"):
                # API 호출
                # API 키는 URL 쿼리 파라미터로 전송
                response = requests.post(f"{API_URL}?key={API_KEY}", json=payload)
                response.raise_for_status() # HTTP 오류 발생 시 예외 발생
                result = response.json()
                
                if result.get('candidates') and result['candidates'][0]['content']['parts']:
                    response_text = result['candidates'][0]['content']['parts'][0]['text']
                    return response_text
                else:
                    raise ValueError("Invalid response structure from API.")
        except Exception as e:
            # 환경 문제로 인한 오류가 반복되므로, 사용자에게 노출되는 메시지는 간결하게 처리합니다.
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return "죄송해요! 지금 Sinu 튜터가 잠시 아파서 대화를 이어갈 수가 없어요. 잠시 후에 다시 시도해 줄래? (API Error)"
    return response_text

# --- 메시지 처리 로직 ---
def process_message(user_input, is_option_click=False):
    """사용자 메시지를 처리하고 AI 응답을 받습니다."""
    if not user_input.strip() and not is_option_click:
        return

    # 옵션 클릭이 아니거나, 헬프 모드 중인 경우에만 사용자 히스토리에 추가
    if not is_option_click or st.session_state.is_help_mode:
        st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
    
    ai_response_text = get_ai_response(st.session_state.chat_history)
    
    # 턴 카운트 증가 (보고서 대기 중이 아니고, 헬프 모드가 아닌 경우에만)
    if not st.session_state.is_report_ready and not st.session_state.is_help_mode:
        st.session_state.turn_count += 1
    
    if ai_response_text.startswith('## FINAL REPORT ##'):
        st.session_state.final_report_text = ai_response_text
        st.session_state.is_report_ready = True
        return 

    # 헬프 모드 상태 업데이트
    if st.session_state.is_help_mode:
        if "이제 너가 한번 써봐!" in ai_response_text:
            st.session_state.is_help_mode = False
    elif "무슨 과목에 대해 이야기하고 싶니? 한국어로 말해줘." in ai_response_text:
        st.session_state.is_help_mode = True

    st.session_state.chat_history.append({"role": "model", "parts": [{"text": ai_response_text}]})
    
    st.rerun()

# --- UI 랜더링 함수 ---

def render_final_report_page():
    """학습 완료 보고서를 시각적으로 보여줍니다."""
    report_text = st.session_state.final_report_text
    if not report_text:
        st.error("오류: 최종 보고서 데이터가 없습니다.")
        return

    # 1. 데이터 추출 (Python 정규표현식 사용)
    quiz_re_match = re.search(r'총 (\d+)문제 중 (\d+)문제를 맞혔습니다', report_text)
    guidance_re_match = re.search(r'문장 완성 지도가 (\d+)회 제공되었습니다', report_text)
    
    total_questions = int(quiz_re_match.group(1)) if quiz_re_match else 4
    correct_answers = int(quiz_re_match.group(2)) if quiz_re_match else 0
    guidance_count = int(guidance_re_match.group(1)) if guidance_re_match else 0
    
    # 2. 보고서 텍스트 정리
    remark_text = report_text.replace("## FINAL REPORT ##", "").strip()
    remark_text = re.sub(r'총 \d+문제 중 \d+문제를 맞혔습니다.', '', remark_text).strip()
    remark_text = re.sub(r'자유 대화 중 문장 완성 지도가 \d+회 제공되었습니다.', '', remark_text).strip()
    
    quiz_percent = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    st.header("학습 완료 보고서!")
    st.markdown(f"**Sinu 튜터와의 신나는 수업 결과를 확인하세요!**")
    
    # 3. 시각화 (Streamlit Markdown 및 HTML/CSS로 스타일링)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div style="background-color: #f3e8ff; border: 2px solid #a78bfa; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #6d28d9; font-weight: bold; font-size: 1.25rem;">[📚] 퀴즈 정답률</h3>
                <p style="font-size: 3rem; font-weight: bold; color: #8b5cf6;">{correct_answers} / {total_questions}</p>
                <div style="width: 100%; height: 20px; background-color: #e5e7eb; border-radius: 10px; overflow: hidden; margin-top: 10px;">
                    <div style="height: 100%; width: {quiz_percent}%; background-color: #10b981; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.875rem;">
                        {quiz_percent:.0f}%
                    </div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background-color: #fffbeb; border: 2px solid #fcd34d; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #d97706; font-weight: bold; font-size: 1.25rem;">[💡] 문장 완성 지도 횟수</h3>
                <p style="font-size: 3rem; font-weight: bold; color: #fbbf24;">{guidance_count} 회</p>
                <p style="font-size: 0.8rem; color: #6b7280; margin-top: 10px;">횟수가 낮을수록 문장 구사가 유창합니다.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown("---")
    
    # 4. Sinu의 코멘트
    st.markdown(
        f"""
        <div style="background-color: #f3f4f6; border-left: 5px solid #6366f1; border-radius: 8px; padding: 15px;">
            <h4 style="color: #4b5563; font-weight: bold; margin-bottom: 5px;">[Sinu] 튜터링 코멘트</h4>
            <p style="color: #374151; white-space: pre-wrap;">{remark_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # 5. 결과 전송 버튼
    if st.button("📧 결과 전송하기", type="primary", use_container_width=True):
        st.success("✅ 전송 완료! 오늘 수업은 여기서 마무리합니다. 안녕! 👋")
        
    st.session_state.is_report_shown = True


def render_chat_page():
    """메인 채팅 인터페이스를 랜더링합니다."""
    
    # 1. 채팅 히스토리 랜더링
    chat_container = st.container(height=450, border=True)
    with chat_container:
        for message in st.session_state.chat_history:
            # 아바타 설정 (이모티콘 사용)
            avatar_char = "⭐" if message["role"] == "model" else "🧑‍🎓"
            
            with st.chat_message(message["role"], avatar=avatar_char):
                text = message["parts"][0]["text"]
                
                # 옵션 파싱 (Phase 1)
                option_marker = "##OPTIONS##:"
                if message["role"] == "model" and option_marker in text:
                    question, options_str = text.split(option_marker)
                    st.markdown(question)
                    
                    # 옵션 버튼을 중앙에 배치하기 위해 columns 사용
                    options = [o.strip() for o in options_str.split('|')]
                    cols = st.columns(len(options))
                    
                    for i, option in enumerate(options):
                        # 버튼 클릭 시 해당 옵션을 사용자 입력으로 처리
                        if cols[i].button(option, key=f"option_{st.session_state.turn_count}_{i}", use_container_width=True):
                            process_message(option, is_option_click=True)
                            
                elif message["role"] == "model":
                    st.markdown(f"**Sinu** | {text}")
                else:
                    st.markdown(text)
    
    # 2. 결과 확인 버튼 (Phase 3 완료 시)
    if st.session_state.is_report_ready:
        st.markdown("---")
        st.markdown("수업이 끝났어요! 🎊 대화 내용과 퀴즈 결과를 정리했어요. 아래 버튼을 눌러서 학습 결과를 확인해 보세요! 👇")
        if st.button("📊 결과 확인하기 (최종 보고서)", type="secondary", use_container_width=True):
            st.session_state.is_report_shown = True
            st.rerun()
        return

    # 3. 입력창 및 버튼 (Phase 1 & 2)
    col_help, col_input, col_send = st.columns([1, 4, 1])
    
    # '모르겠어요' 버튼 (Phase 2에서만 활성화)
    is_conversation_phase = st.session_state.turn_count >= 4
    
    if col_help.button("모르겠어요 🇰🇷", key="help_button", disabled=not is_conversation_phase or st.session_state.is_help_mode, use_container_width=True):
        process_message("ACTION: NEED SUBJECT NAME HELP", is_option_click=True)
        
    # 사용자 입력
    user_input = col_input.text_input(
        "여기에 답변을 입력해 주세요!", 
        key="user_input_key", 
        placeholder="영어로 답변을 입력하거나 '모르겠어요' 버튼을 눌러보세요.",
        label_visibility="collapsed",
        disabled=st.session_state.is_report_ready
    )
    
    # 전송 버튼
    if col_send.button("Send", type="primary", disabled=st.session_state.is_report_ready, use_container_width=True):
        if user_input:
            process_message(user_input)
        
    # Streamlit은 Enter 키 처리를 자동으로 수행하므로, 별도의 Enter 키 이벤트 핸들링은 필요하지 않습니다.


# --- 메인 앱 실행 ---
def app_main():
    """Streamlit 애플리케이션의 메인 진입점"""
    
    # Streamlit의 메인 루프에서 실행될 내용 결정
    if st.session_state.is_report_shown:
        render_final_report_page()
    else:
        render_chat_page()

if __name__ == "__main__":
    app_main()

