import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="신나는 초등 과학 실험실",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 초등 과학 실험 챗봇")
st.markdown("식물의 성장 실험 데이터를 기록하고, 결과를 분석해 드립니다.")


# --- Data Management Functions ---
# Use a clear filename
DATA_FILE = "plant_growth_data.csv"

def load_data():
    """Loads data from CSV file or creates an empty DataFrame."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    # Define columns explicitly for a fresh start
    return pd.DataFrame(columns=["날짜", "그룹", "식물 키(cm)", "메모"])

def save_data():
    """Saves the current session data to the CSV file."""
    if 'plant_data' in st.session_state:
        st.session_state.plant_data.to_csv(DATA_FILE, index=False, encoding='utf-8')

# --- Session State Initialization ---
if 'plant_data' not in st.session_state:
    st.session_state.plant_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 🙋‍♂️ 저는 여러분의 과학 실험 도우미 챗봇이에요. 무엇을 도와드릴까요? 아래에서 **'실험 기록하기'** 또는 **'결과 보기'**를 선택해주세요."}
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
    """Displays the data recording form."""
    with st.chat_message("assistant"):
        st.write("🌿 식물 성장 관찰일지를 기록합니다. 빈칸을 채워주세요!")
        
        # Use a key to prevent form submission from interfering with other elements
        with st.form("data_form", clear_on_submit=True): 
            observation_date = st.date_input("🗓️ 관찰 날짜", value=datetime.now(), key="obs_date")
            plant_group = st.selectbox("🌱 식물 그룹 선택 (실험 조건)", ("☀️ 햇빛 드는 곳", "🌑 어두운 옷장"), key="group_select")
            
            # Ensure number input has correct step/format for elementary level
            plant_height = st.number_input("📏 식물의 키 (cm)", min_value=0.0, step=0.1, format="%.1f", key="height_input")
            
            memo = st.text_area("📝 기타 관찰 내용 (색깔, 잎의 수 등)", key="memo_input")
            
            submitted = st.form_submit_button("✅ 기록 제출하기")

            if submitted:
                if plant_height <= 0.0:
                    st.error("식물 키는 0cm보다 커야 합니다.")
                else:
                    formatted_date = observation_date.strftime("%Y-%m-%d")
                    new_data = pd.DataFrame(
                        [[formatted_date, plant_group, plant_height, memo]],
                        columns=["날짜", "그룹", "식물 키(cm)", "메모"]
                    )
                    
                    # Concatenate new data and save
                    st.session_state.plant_data = pd.concat([st.session_state.plant_data, new_data], ignore_index=True)
                    save_data()
                    
                    # Update chat message
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ {formatted_date}의 관찰 기록(키: {plant_height}cm, 그룹: {plant_group})이 성공적으로 저장되었습니다! 다음 관찰은 언제 하실 건가요?"})
                    
                    # Rerun to clear the form and update chat
                    st.session_state.show_record_form = False # Hide the form
                    st.rerun()

def show_results():
    """Displays results, analysis, and educational interpretation."""
    
    df = st.session_state.plant_data.copy()
    
    if df.empty:
        response_content = "아직 기록된 데이터가 없어요. 😢 먼저 '실험 기록하기' 버튼을 눌러 관찰한 내용을 기록해주세요."
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun() 
        return

    # Data Preparation for Analysis and Charting
    df['날짜'] = pd.to_datetime(df['날짜'])
    df = df.sort_values(by="날짜")
    
    # Calculate the average height for each group on each date
    pivot_df = df.pivot_table(index='날짜', columns='그룹', values='식물 키(cm)', aggfunc='mean')

    # --- Educational Analysis ---
    
    # 1. Get the latest observation date and average heights for interpretation
    latest_date = df['날짜'].max()
    latest_data = df[df['날짜'] == latest_date]
    avg_heights = latest_data.groupby('그룹')['식물 키(cm)'].mean()

    sun_avg = avg_heights.get("☀️ 햇빛 드는 곳", 0)
    dark_avg = avg_heights.get("🌑 어두운 옷장", 0)
    
    # 2. Generate Educational Interpretation
    if sun_avg > dark_avg * 1.5 and sun_avg > 1: # Significant difference (Sunlight is winning)
        interpretation = (
            f"대단해요! ✨ 실험 결과, '☀️ 햇빛 드는 곳' 그룹의 평균 키가 약 **{sun_avg:.1f}cm**로, "
            f"'🌑 어두운 옷장' 그룹의 **{dark_avg:.1f}cm**보다 훨씬 컸어요! 🎉\n\n"
            "이것은 바로 **광합성** 때문이에요. [Image of Photosynthesis process]\n"
            "식물은 햇빛을 받아 물과 이산화탄소를 이용해 스스로 양분(먹을 것)을 만들고 쑥쑥 자랍니다. "
            "햇빛이 없으면 양분을 만들기 어려워 잘 자라지 못하는 것이지요. "
            "이 실험으로 **식물이 자라는 데 햇빛이 꼭 필요하다**는 중요한 과학적 사실을 알게 되었어요!"
        )
    elif sun_avg > dark_avg: # Slight difference
        interpretation = (
            f"실험 결과를 보니 '☀️ 햇빛 드는 곳' 그룹이 '🌑 어두운 옷장' 그룹보다 조금 더 잘 자랐어요. "
            "두 그룹 모두 잘 자라고 있지만, 햇빛이 있는 그룹이 조금 더 활발하게 광합성을 했을 거예요. "
            "다음에는 다른 환경(예: 물의 양)을 다르게 해서 실험해 보면 어떨까요? 🤔"
        )
    elif sun_avg < dark_avg: # Unexpected result
        interpretation = (
            "흥미롭네요! 예상과 달리 '🌑 어두운 옷장' 그룹이 더 잘 자랐어요. 혹시 빛이 없는 환경에 적합한 특별한 식물이었을까요? "
            "아니면 혹시 관찰 과정에서 다른 요인(온도, 물 주기)에 차이가 있었는지 다시 한번 확인해 보는 것이 좋아요! 과학은 가설을 검증하는 과정이니까요!🧐"
        )
    else:
        interpretation = "두 그룹의 성장에 현재까지 큰 차이가 없네요. 아마도 실험 기간이 짧거나, 기록을 시작한 지 얼마 되지 않았을 수 있어요. 조금 더 오래 관찰해 봅시다!"

    # --- Construct and Display Response ---
    response_content = f"📊 **실험 결과 분석 리포트**\n\n{interpretation}\n\n**🔍 전체 데이터도 한번 살펴볼까요?**"
    
    # Append educational message and chart data to the chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "chart_data": pivot_df, 
        "dataframe": df.astype({'날짜': str}) # Convert datetime back to string for clean display
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
        response_content = "죄송해요. 😥 저는 지금 '식물 성장 기록'과 '실험 결과 보기'만 할 수 있어요. 둘 중 하나를 선택하거나, 아래 버튼을 눌러주세요!"
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
