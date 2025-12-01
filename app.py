import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="🔥 열의 이동과 단열 실험실",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 열의 이동과 단열 실험 챗봇")
st.markdown("다른 조건의 컵에 담긴 물의 온도 변화를 기록하고, 단열 효과를 분석해 드립니다.")


# --- Data Management Functions ---
# Use a clear filename
DATA_FILE = "insulation_experiment_data.csv"

def load_data():
    """CSV 파일에서 데이터를 로드하거나 비어있는 DataFrame을 생성합니다."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    # 실험 주제에 맞게 컬럼명 변경: 식물 키(cm) -> 온도(°C)
    return pd.DataFrame(columns=["날짜 및 시간", "그룹", "온도(°C)", "메모"])

def save_data():
    """현재 세션 데이터를 CSV 파일에 저장합니다."""
    if 'experiment_data' in st.session_state:
        st.session_state.experiment_data.to_csv(DATA_FILE, index=False, encoding='utf-8')

# --- Session State Initialization ---
if 'experiment_data' not in st.session_state:
    st.session_state.experiment_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 🙋‍♂️ 저는 여러분의 단열 실험 도우미 챗봇이에요. 따뜻한 물이 얼마나 오랫동안 따뜻하게 유지되는지 함께 관찰해 봅시다! 아래에서 **'실험 기록하기'** 또는 **'결과 분석 보기'**를 선택해주세요."}
    ]
# State to manage showing the form directly in the main interface
if 'show_record_form' not in st.session_state:
    st.session_state.show_record_form = False

# --- Chat History Display ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # Display DataFrame if included in the message
        if "dataframe" in message:
            st.dataframe(message["dataframe"])
        
        # Display Chart if included in the message
        if "chart_data" in message:
            # We use a try-except block here for safety in case of bad data
            try:
                st.line_chart(message["chart_data"])
            except Exception as e:
                st.error(f"⚠️ 그래프를 그리는 중 오류가 발생했습니다: {e}")


# --- Chatbot Functions ---

def display_record_form():
    """데이터 기록 폼을 표시합니다."""
    with st.chat_message("assistant"):
        st.write("📝 **열 변화 관찰 기록**을 시작합니다. 빈칸을 채워주세요!")
        
        with st.form("data_form", clear_on_submit=True): 
            # 날짜와 시간을 동시에 기록하여 시간 경과에 따른 변화를 정확히 측정
            observation_datetime = st.datetime_input("🗓️ 관찰 날짜 및 시간", value=datetime.now(), key="obs_datetime")
            
            # 단열 실험 조건으로 그룹 변경
            experiment_group = st.selectbox("🧪 실험 그룹 선택 (실험 조건)", ("🔥 따뜻한 담요 컵 (단열)", "🧊 그냥 컵 (대조군)"), key="group_select")
            
            # 온도 측정으로 항목 변경
            water_temp = st.number_input("🌡️ 물의 현재 온도 (°C)", min_value=10.0, step=0.1, format="%.1f", key="temp_input")
            
            memo = st.text_area("📝 기타 관찰 내용 (물의 상태, 외부 환경 등)", key="memo_input")
            
            submitted = st.form_submit_button("✅ 기록 제출하기")

            if submitted:
                if water_temp < 10.0:
                    st.error("온도는 10°C 이상이어야 합니다.")
                else:
                    # 날짜와 시간을 문자열로 포맷팅
                    formatted_datetime = observation_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    new_data = pd.DataFrame(
                        [[formatted_datetime, experiment_group, water_temp, memo]],
                        columns=["날짜 및 시간", "그룹", "온도(°C)", "메모"]
                    )
                    
                    # 데이터 통합 및 저장
                    st.session_state.experiment_data = pd.concat([st.session_state.experiment_data, new_data], ignore_index=True)
                    save_data()
                    
                    # 챗봇 응답 메시지 업데이트
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ {formatted_datetime}의 관찰 기록(온도: {water_temp}°C, 그룹: {experiment_group})이 성공적으로 저장되었습니다! 다음 관찰은 언제 하실 건가요?"})
                    
                    # 폼 숨기고 채팅 업데이트를 위해 새로고침
                    st.session_state.show_record_form = False 
                    st.rerun()

def show_results():
    """결과 그래프, 분석, 교육적 해석을 표시합니다."""
    
    df = st.session_state.experiment_data.copy()
    
    if df.empty:
        response_content = "아직 기록된 데이터가 없어요. 😢 먼저 '실험 기록하기' 버튼을 눌러 관찰한 내용을 기록해주세요."
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun() 
        return

    # Data Preparation for Analysis and Charting
    df['날짜 및 시간'] = pd.to_datetime(df['날짜 및 시간'])
    df = df.sort_values(by="날짜 및 시간")
    
    # 시간 순서대로 각 그룹의 평균 온도 계산
    pivot_df = df.pivot_table(index='날짜 및 시간', columns='그룹', values='온도(°C)', aggfunc='mean')

    # --- Educational Analysis (단열 효과 분석) ---
    
    # 두 그룹 모두 데이터가 있는지 확인
    groups = pivot_df.columns
    if len(groups) < 2 or pivot_df.shape[0] < 2:
        interpretation = "두 그룹을 모두 기록하거나 충분한 시간이 지나야 정확한 분석이 가능합니다. 🧐 온도를 더 자주 기록해보세요!"
    else:
        # 각 그룹의 총 온도 변화 (가장 높은 온도 - 가장 낮은 온도) 계산
        initial_temp = pivot_df.iloc[0].mean() # 실험 시작 시점의 평균 온도 (시작 온도가 비슷하다고 가정)
        
        # 마지막 관찰 시점의 온도
        last_temp = pivot_df.iloc[-1]
        
        # 마지막 관찰 시점의 온도 감소량 (시작 온도가 동일하다는 가정 하에 단순 비교)
        insulated_temp = last_temp.get("🔥 따뜻한 담요 컵 (단열)", np.nan)
        control_temp = last_temp.get("🧊 그냥 컵 (대조군)", np.nan)
        
        # 유효한 데이터가 있을 때만 분석 수행
        if pd.notna(insulated_temp) and pd.notna(control_temp):
            
            # 챗봇의 중요성 강조: 실시간 분석!
            time_elapsed = (df['날짜 및 시간'].max() - df['날짜 및 시간'].min()).total_seconds() / 60
            
            if insulated_temp > control_temp * 1.05: # 단열 컵이 5% 이상 온도가 더 높을 때
                temp_diff = insulated_temp - control_temp
                interpretation = (
                    f"대단해요! ✨ **{time_elapsed:.1f}분**이 지난 후,\n"
                    f"'🔥 따뜻한 담요 컵'의 온도는 **{insulated_temp:.1f}°C**로, '🧊 그냥 컵'의 **{control_temp:.1f}°C**보다 "
                    f"약 **{temp_diff:.1f}°C** 더 높게 유지되었어요! 🎉\n\n"
                    "이것은 **단열**이 잘 되었기 때문이에요. 컵을 덮은 담요가 외부로 **열이 이동하는 것**을 막아주었답니다. "
                    "단열재는 열이 밖으로 새어 나가는 속도를 늦춰서 물을 더 오랫동안 따뜻하게 보존해 주는 중요한 역할을 해요. "
                    "이 실험으로 **단열의 과학적 원리**를 확인했어요!"
                )
            elif control_temp > insulated_temp * 1.05: # 예상 밖의 결과
                interpretation = (
                    f"흥미롭네요! **{time_elapsed:.1f}분** 후, '🧊 그냥 컵'의 온도가 '🔥 따뜻한 담요 컵'보다 더 높게 나왔어요. 🧐\n\n"
                    "혹시 사용한 담요가 충분히 단열이 잘 되지 않았거나, 두 컵의 시작 온도가 달랐을까요? "
                    "실험은 가설을 검증하는 과정이에요. 원인을 찾기 위해 **실험 조건을 다시 한번 확인**하거나, 다른 단열재로 바꿔서 실험해 보는 것이 좋겠어요!"
                )
            else:
                interpretation = (
                    "두 컵의 온도 변화가 현재까지 비슷하네요. 아마도 실험이 시작된 지 얼마 되지 않았을 수 있어요. "
                    "열의 이동을 확인하려면 조금 더 오래 관찰이 필요해요! ⏰"
                )
        else:
            interpretation = "데이터가 부족하여 정확한 분석을 할 수 없습니다. 두 그룹의 관찰 기록을 모두 입력해주세요."


    # --- Construct and Display Response ---
    response_content = f"📊 **실시간 열 변화 분석 리포트**\n\n{interpretation}\n\n**📈 관찰 시간 경과에 따른 온도 변화 그래프**"
    
    # Append educational message and chart data to the chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "chart_data": pivot_df, 
        "dataframe": df.astype({'날짜 및 시간': str}) # Convert datetime back to string for clean display
    })
    
    # Clear and rerun to ensure the chat history is fully updated and displayed
    st.rerun()


# --- Main Interaction Logic ---

# Handle user input from the chat bar
if prompt := st.chat_input("무엇을 하시겠어요? ('기록' 또는 '결과 보기'라고 입력해보세요)"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.show_record_form = False # Hide form if chat is active
    
    # Simple keyword routing for the chatbot
    if "기록" in prompt:
        st.session_state.show_record_form = True
    elif "결과" in prompt or "보기" in prompt or "분석" in prompt:
        show_results()
    else:
        # Generic response
        response_content = "죄송해요. 😥 저는 지금 '열 변화 기록'과 '실험 결과 분석'만 할 수 있어요. 둘 중 하나를 선택하거나, 아래 버튼을 눌러주세요!"
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun()


# --- Initial Screen and Button Display ---

# Only show action buttons if the form is not open AND it's the start or the last message was a response
if not st.session_state.show_record_form and st.session_state.messages[-1]["role"] == "assistant":
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 실험 기록하기", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "실험 기록하기 버튼을 눌렀어요."})
            st.session_state.show_record_form = True # Toggle state to show form
            st.rerun()
    with col2:
        if st.button("📈 결과 분석 보기", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "결과 분석 보기 버튼을 눌렀어요."})
            show_results()

# Display the form if the state is set (e.g., after button click)
if st.session_state.show_record_form:
    display_record_form()
