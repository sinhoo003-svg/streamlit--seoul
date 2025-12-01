import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="🔥 열의 이동과 단열 실험실 - 실시간 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 실시간 열 변화 분석 챗봇")
st.markdown("손으로 하기 어려운 **냉각 속도(Cooling Rate)를 즉시 계산**하여, 단열 효과를 과학적으로 증명해 드립니다.")


# --- Data Management Functions ---
# Use a clear filename
DATA_FILE = "insulation_experiment_data.csv"

def load_data():
    """CSV 파일에서 데이터를 로드하거나 비어있는 DataFrame을 생성합니다."""
    if os.path.exists(DATA_FILE):
        # dtype을 지정하여 데이터 로드 시 온도 컬럼을 float으로 강제 변환하여 안정성을 높임
        return pd.read_csv(DATA_FILE, dtype={'온도(°C)': np.float64})
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
                st.error(f"⚠️ 그래프를 그리는 중 오류가 발생했습니다. 데이터를 확인해주세요: {e}")


# --- Chatbot Functions ---

def display_record_form():
    """데이터 기록 폼을 표시합니다."""
    with st.chat_message("assistant"):
        st.write("📝 **열 변화 관찰 기록**을 시작합니다. 빈칸을 채워주세요!")
        
        with st.form("data_form", clear_on_submit=True): 
            # 날짜와 시간을 동시에 기록하여 시간 경과에 따른 변화를 정확히 측정 (st.datetime_input 오류 방지를 위해 분리)
            now = datetime.now()
            observation_date = st.date_input("🗓️ 관찰 날짜", value=now.date(), key="obs_date")
            observation_time = st.time_input("⏱️ 관찰 시간", value=now.time(), key="obs_time")
            
            # Combine date and time inputs into one datetime object
            observation_datetime = datetime.combine(observation_date, observation_time)
            
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

def calculate_cooling_rate(group_data):
    """주어진 그룹 데이터에 대해 냉각 속도(C/min)를 계산합니다."""
    if len(group_data) < 2:
        return np.nan
    
    # 가장 오래된 기록과 가장 최신 기록을 찾습니다.
    start_record = group_data.iloc[0]
    end_record = group_data.iloc[-1]
    
    time_diff_seconds = (end_record['날짜 및 시간'] - start_record['날짜 및 시간']).total_seconds()
    temp_diff = start_record['온도(°C)'] - end_record['온도(°C)']
    
    if time_diff_seconds <= 60:
        return np.nan # 1분 미만은 정확도 문제로 분석하지 않음

    # 냉각 속도 = 온도 변화 / 시간 변화 (분당 온도 하락)
    cooling_rate = temp_diff / (time_diff_seconds / 60)
    return cooling_rate

def show_results():
    """결과 그래프, 분석, 교육적 해석을 표시합니다."""
    
    df = st.session_state.experiment_data.copy()
    
    if df.empty:
        response_content = "아직 기록된 데이터가 없어요. 😢 먼저 '실험 기록하기' 버튼을 눌러 관찰한 내용을 기록해주세요."
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun() 
        return

    # --- 데이터 전처리 및 분석 시작 ---
    try:
        # Data Preparation for Analysis and Charting
        df['날짜 및 시간'] = pd.to_datetime(df['날짜 및 시간'], errors='coerce')
        df.dropna(subset=['날짜 및 시간'], inplace=True)
        df = df.sort_values(by="날짜 및 시간")
        
        # 시간 순서대로 각 그룹의 평균 온도 계산 (그래프 출력용)
        pivot_df = df.pivot_table(index='날짜 및 시간', columns='그룹', values='온도(°C)', aggfunc='mean')

        # --- Educational Analysis (단열 효과 분석) ---
        
        # 각 그룹별로 데이터 그룹화
        insulated_data = df[df['그룹'] == "🔥 따뜻한 담요 컵 (단열)"]
        control_data = df[df['그룹'] == "🧊 그냥 컵 (대조군)"]
        
        # 냉각 속도 계산
        insulated_rate = calculate_cooling_rate(insulated_data)
        control_rate = calculate_cooling_rate(control_data)
        
        cooling_summary = {
            '그룹': ["🔥 따뜻한 담요 컵 (단열)", "🧊 그냥 컵 (대조군)"],
            '분당 냉각 속도 (℃/분)': [insulated_rate, control_rate]
        }
        cooling_df = pd.DataFrame(cooling_summary).set_index('그룹')
        
        
        # 분석 결과 해석
        if pd.notna(insulated_rate) and pd.notna(control_rate):
            
            if insulated_rate < control_rate * 0.9: # 단열 컵의 냉각 속도가 10% 이상 느릴 때
                rate_diff = control_rate - insulated_rate
                
                # **초등 수준에 맞춰 해석 단순화 및 시각 자료 요청**
                interpretation = (
                    f"✨ **실시간 과학 분석 결과:**\n\n"
                    f"챗봇이 계산한 결과, 담요 컵은 **1분마다 {insulated_rate:.2f}°C**의 열을 잃었고, "
                    f"그냥 컵은 **1분마다 {control_rate:.2f}°C**의 열을 잃었어요. "
                    f"담요 컵이 약 **{rate_diff:.2f}°C**만큼 **열을 더 천천히 잃은** 거예요! 🎉\n\n"
                    "이것은 **단열재**가 열이 밖으로 나가는 길을 막아주기 때문이랍니다. 온도를 지켜주는 벽처럼 말이죠! "
                    "단열의 원리를 그림으로 확인해 보세요! "
                )
            elif insulated_rate > control_rate * 1.1: # 예상 밖의 결과
                interpretation = (
                    f"흥미롭네요! 🧐 챗봇이 계산한 결과, '🔥 따뜻한 담요 컵'의 냉각 속도({insulated_rate:.2f}°C/분)가 "
                    f"'🧊 그냥 컵'({control_rate:.2f}°C/분)보다 더 빨라요! 이 결과는 우리의 예상(가설)과 반대됩니다.\n\n"
                    "이런 경우, 챗봇은 **실험 조건을 다시 확인**하라고 알려줍니다. 혹시 담요를 덮는 과정에서 물이 쏟아져 온도가 빨리 변했거나, 담요 자체가 열을 잘 전달하는 물질이었을까요? 원인을 찾아봅시다!"
                )
            else:
                interpretation = (
                    "두 컵의 열 손실 속도가 현재까지 비슷하네요. 냉각 속도 차이가 크지 않을 수 있어요. "
                    "단열 효과가 미미하거나, 아직 충분한 시간 동안 기록되지 않았을 수 있습니다. ⏰ **10분 후**에 다시 기록하고 분석해 보세요!"
                )
        else:
            interpretation = "정확한 냉각 속도 분석을 위해서는 각 그룹별로 **최소 1분 이상의 간격**을 두고 **2회 이상** 관찰한 기록이 필요합니다. ⏱️"

    except Exception as e:
        # 데이터 처리 중 발생하는 예상치 못한 오류를 잡아 사용자에게 안내
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ **데이터 분석 중 심각한 오류가 발생했습니다.** 😭\n\n데이터 파일(`{DATA_FILE}`)의 내용이 손상되었을 수 있습니다. 기존 데이터를 지우고 새로 실험 기록을 시작하거나, 데이터를 다운로드하여 내용을 확인해 주세요. 오류 상세 내용: `{e}`"
        })
        st.rerun()
        return


    # --- Construct and Display Response ---
    response_content = f"📊 **실시간 열 변화 분석 리포트**\n\n{interpretation}\n\n**✅ 챗봇 분석 요약: 분당 냉각 속도**"
    
    # Append educational message and chart data to the chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "chart_data": pivot_df, 
        "dataframe": cooling_df # 냉각 속도 분석 테이블 추가
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
