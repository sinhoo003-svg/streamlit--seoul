import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np
import time 

# --- Configuration ---
st.set_page_config(
    page_title="💧 물이 사라지는 속도 마법사",
    page_icon="💧",
    layout="wide"
)

st.title("💧 물이 사라지는 속도 마법사")
st.markdown("햇빛, 그늘, 바람 등 다른 조건에 따른 **물의 증발 속도를 즉시 계산**하고 비교하여 분석해 드립니다.")


# --- Data Management Functions ---
DATA_FILE = "evaporation_experiment_data.csv"

def load_data():
    """CSV 파일에서 데이터를 로드하거나 비어있는 DataFrame을 생성합니다."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, dtype={'수위(mm)': np.float64})
    # 실험 주제에 맞게 컬럼명 변경: 수위(mm)
    return pd.DataFrame(columns=["날짜 및 시간", "조건 (그룹)", "수위(mm)", "메모"])

def save_data():
    """현재 세션 데이터를 CSV 파일에 저장합니다."""
    if 'experiment_data' in st.session_state:
        st.session_state.experiment_data.to_csv(DATA_FILE, index=False, encoding='utf-8')

# --- Session State Initialization ---
if 'experiment_data' not in st.session_state:
    st.session_state.experiment_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 🙋‍♂️ 저는 여러분의 물 마법 도우미 챗봇이에요. 물이 얼마나 빨리 사라지는지 함께 관찰해 봅시다! 아래에서 **'관찰 기록하기'** 또는 **'결과 분석 보기'**를 선택해주세요."}
    ]
if 'show_record_form' not in st.session_state:
    st.session_state.show_record_form = False

# --- Chat History Display ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        if "dataframe" in message:
            st.dataframe(message["dataframe"])
        
        if "chart_data" in message:
            try:
                # 증발은 시간에 따른 변화이므로 라인 차트 사용
                st.line_chart(message["chart_data"]) 
            except Exception as e:
                st.error(f"⚠️ 그래프를 그리는 중 오류가 발생했습니다. 데이터를 확인해주세요: {e}")


# --- Chatbot Functions ---

def display_record_form():
    """데이터 기록 폼을 표시합니다."""
    with st.chat_message("assistant"):
        st.write("📝 **물의 높이(수위) 측정 기록**을 시작합니다. 몇 mm인가요?")
        
        with st.form("data_form", clear_on_submit=True): 
            now = datetime.now()
            observation_date = st.date_input("🗓️ 관찰 날짜", value=now.date(), key="obs_date")
            observation_time = st.time_input("⏱️ 관찰 시간", value=now.time(), key="obs_time")
            observation_datetime = datetime.combine(observation_date, observation_time)
            
            # 실험 조건 그룹 선택
            condition = st.selectbox("🧪 실험 조건 (그룹)", ("☀️ 햇빛이 잘 드는 곳", "☁️ 그늘진 곳", "💨 선풍기 바람이 부는 곳"), key="group_select")
            
            # 수위 측정 항목
            water_level = st.number_input("📏 물의 현재 수위 (mm)", min_value=1.0, step=1.0, format="%d", key="water_level")
            
            memo = st.text_area("📝 기타 관찰 내용 (날씨, 바람 세기 등)", key="memo_input")
            
            submitted = st.form_submit_button("✅ 기록 제출하기")

            if submitted:
                if water_level < 1:
                    st.error("수위는 1mm 이상이어야 합니다.")
                else:
                    formatted_datetime = observation_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    new_data = pd.DataFrame(
                        [[formatted_datetime, condition, water_level, memo]],
                        columns=["날짜 및 시간", "조건 (그룹)", "수위(mm)", "메모"]
                    )
                    
                    st.session_state.experiment_data = pd.concat([st.session_state.experiment_data, new_data], ignore_index=True)
                    save_data()
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ {formatted_datetime}의 관찰 기록(수위: {water_level}mm, 조건: {condition})이 저장되었습니다! 다음 관찰을 기록해보세요."})
                    
                    st.session_state.show_record_form = False 
                    st.rerun()

def calculate_evaporation_rate(group_data):
    """주어진 그룹 데이터에 대해 평균 증발 속도(mm/day)를 계산합니다."""
    if len(group_data) < 2:
        return np.nan
    
    # 가장 오래된 기록과 가장 최신 기록을 찾습니다.
    start_record = group_data.iloc[0]
    end_record = group_data.iloc[-1]
    
    time_diff_seconds = (end_record['날짜 및 시간'] - start_record['날짜 및 시간']).total_seconds()
    
    if time_diff_seconds == 0:
        return np.nan # 시간이 지나지 않았으면 계산 불가
        
    # 증발된 물의 양
    evaporated_amount = start_record['수위(mm)'] - end_record['수위(mm)']
    
    # 시간 변화 (일 단위)
    time_diff_days = time_diff_seconds / (60 * 60 * 24)
    
    if time_diff_days <= 0 or evaporated_amount < 0:
        return np.nan # 시간 순서가 잘못되었거나 물이 늘어난 경우 (측정 오류)
    
    # 증발 속도 = 증발량 / 시간 변화 (mm/day)
    evaporation_rate = evaporated_amount / time_diff_days
    return evaporation_rate

def show_results():
    """결과 그래프, 분석, 교육적 해석을 표시합니다."""
    
    df = st.session_state.experiment_data.copy()
    
    if df.empty:
        response_content = "아직 기록된 실험이 없어요. 😢 먼저 '관찰 기록하기' 버튼을 눌러 물의 높이를 기록해주세요."
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun() 
        return

    # --- 데이터 전처리 및 분석 시작 ---
    try:
        # Data Preparation for Analysis and Charting
        df['날짜 및 시간'] = pd.to_datetime(df['날짜 및 시간'], errors='coerce')
        df.dropna(subset=['날짜 및 시간'], inplace=True)
        df = df.sort_values(by="날짜 및 시간")
        
        # 시간 순서대로 각 그룹의 평균 수위 계산 (그래프 출력용)
        pivot_df = df.pivot_table(index='날짜 및 시간', columns='조건 (그룹)', values='수위(mm)', aggfunc='mean')

        # --- Educational Analysis (증발 속도 분석) ---
        
        # 그룹별 데이터 그룹화 및 속도 계산
        groups = df['조건 (그룹)'].unique()
        rate_data = []
        
        for group in groups:
            group_data = df[df['조건 (그룹)'] == group].sort_values('날짜 및 시간')
            rate = calculate_evaporation_rate(group_data)
            rate_data.append({'조건 (그룹)': group, '평균 증발 속도 (mm/일)': rate})
            
        rate_df = pd.DataFrame(rate_data).set_index('조건 (그룹)').round(2)
        
        
        # 분석 결과 해석
        valid_rates = rate_df.dropna()
        
        if valid_rates.empty or len(valid_rates) < 2:
            interpretation = "정확한 증발 속도 분석을 위해서는 각 그룹별로 **최소 2회 이상** 관찰한 기록이 필요합니다. ⏱️"
        else:
            # 가장 빠른 증발 속도 조건 찾기
            fastest_rate = valid_rates['평균 증발 속도 (mm/일)'].max()
            fastest_group = valid_rates['평균 증발 속도 (mm/일)'].idxmax()
            
            # 초등학생 눈높이에 맞춘 해석 (3~4학년 수준)
            interpretation = (
                f"🎉 **물이 사라지는 마법 분석 결과!**\n\n"
                f"챗봇이 계산한 결과, 물이 **가장 빨리 사라진** 곳은 **'{fastest_group}'** 이며, 하루에 평균 **{fastest_rate:.1f}mm**씩 사라졌어요! \n\n"
                f"왜 그럴까요? 물은 **뜨거운 열**을 받거나, **바람**이 불 때 빨리 사라진답니다. 햇빛은 물을 뜨겁게 하고, 바람은 물이 날아가는 것을 도와줘요. \n\n"
                f"**그래프**를 보면 어떤 그룹의 물이 가장 빨리 줄어들었는지 눈으로 확인할 수 있을 거예요!"
            )
            
            # 가장 느린 그룹 (보너스 해석)
            slowest_rate = valid_rates['평균 증발 속도 (mm/일)'].min()
            slowest_group = valid_rates['평균 증발 속도 (mm/일)'].idxmin()
            
            if fastest_group != slowest_group:
                interpretation += (
                    f"\n\n반대로, **'{slowest_group}'**에서는 하루에 **{slowest_rate:.1f}mm**씩 사라져 물이 **가장 오래 남아있었어요**. "
                    f"이곳은 물이 뜨거워지기 어렵거나, 바람이 잘 불지 않는 곳이었겠죠?"
                )
            

    except Exception as e:
        # 데이터 처리 중 발생하는 예상치 못한 오류를 잡아 사용자에게 안내
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ **데이터 분석 중 심각한 오류가 발생했습니다.** 😭\n\n데이터 파일(`{DATA_FILE}`)의 내용이 손상되었을 수 있습니다. 오류 상세 내용: `{e}`"
        })
        st.rerun()
        return


    # --- Construct and Display Response ---
    response_content = f"📊 **실시간 물 증발 속도 분석 리포트**\n\n{interpretation}\n\n**✅ 챗봇 분석 요약: 하루 평균 증발 속도**"
    
    # Append educational message and chart data to the chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "chart_data": pivot_df, # 수위 변화 라인 차트
        "dataframe": rate_df.astype(str) # 분석 테이블
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
    if "기록" in prompt or "관찰" in prompt:
        st.session_state.show_record_form = True
    elif "결과" in prompt or "보기" in prompt or "분석" in prompt:
        show_results()
    else:
        # Generic response
        response_content = "죄송해요. 😥 저는 지금 '관찰 기록'과 '결과 분석'만 할 수 있어요. 둘 중 하나를 선택하거나, 아래 버튼을 눌러주세요!"
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun()


# --- Initial Screen and Button Display ---

# Only show action buttons if the form is not open AND it's the start or the last message was a response
if not st.session_state.show_record_form and st.session_state.messages[-1]["role"] == "assistant":
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 관찰 기록하기", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "관찰 기록하기 버튼을 눌렀어요."})
            st.session_state.show_record_form = True # Toggle state to show form
            st.rerun()
    with col2:
        if st.button("📈 결과 분석 보기", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "결과 분석 보기 버튼을 눌렀어요."})
            show_results()

# Display the form if the state is set (e.g., after button click)
if st.session_state.show_record_form:
    display_record_form()
