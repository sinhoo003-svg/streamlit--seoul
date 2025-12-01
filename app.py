import streamlit as st
import pandas as pd
from datetime import datetime
import os
import numpy as np

# --- Configuration ---
st.set_page_config(
    page_title="⏱️ 용해 속도 마법사 (40분 실험)",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 용해 속도 비교 분석 챗봇")
st.markdown("뜨거운 물과 찬물에서 설탕이 녹는 시간을 기록하면, 챗봇이 **평균 속도**를 계산해 드립니다. (5학년 1학기 '용해와 용액' 참고)")


# --- Data Management Functions ---
DATA_FILE = "dissolving_experiment_data.csv"

def load_data():
    """CSV 파일에서 데이터를 로드하거나 비어있는 DataFrame을 생성합니다."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, dtype={'용해 시간(초)': np.float64})
    # 실험 주제에 맞게 컬럼명 변경: 용해 시간(초)
    return pd.DataFrame(columns=["날짜 및 시간", "조건 (그룹)", "용해 시간(초)", "메모"])

def save_data():
    """현재 세션 데이터를 CSV 파일에 저장합니다."""
    if 'experiment_data' not in st.session_state:
        st.error("데이터 저장 오류: experiment_data가 세션에 없습니다.")
        return
    st.session_state.experiment_data.to_csv(DATA_FILE, index=False, encoding='utf-8')

# --- Session State Initialization ---
if 'experiment_data' not in st.session_state:
    st.session_state.experiment_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 🙋‍♂️ 저는 여러분의 용해 실험 도우미 챗봇이에요. 설탕이 얼마나 빨리 녹는지 함께 측정해 봅시다! 아래에서 **'실험 기록하기'** 또는 **'결과 분석 보기'**를 선택해주세요."}
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
                # 그룹별 평균 용해 시간 비교는 막대 그래프가 효과적
                st.bar_chart(message["chart_data"]) 
            except Exception as e:
                st.error(f"⚠️ 그래프를 그리는 중 오류가 발생했습니다. 데이터를 확인해주세요: {e}")


# --- Chatbot Functions ---

def display_record_form():
    """데이터 기록 폼을 표시합니다."""
    with st.chat_message("assistant"):
        st.write("📝 **설탕 용해 시간 측정 기록**을 시작합니다.")
        
        with st.form("data_form", clear_on_submit=True): 
            now = datetime.now()
            observation_datetime = datetime.combine(now.date(), now.time())
            
            # 실험 조건 그룹 선택 (온도)
            condition = st.selectbox("🧪 실험 조건 (그룹)", ("🔥 뜨거운 물", "🧊 찬 물"), key="group_select")
            
            # 용해 시간 측정 항목
            dissolving_time = st.number_input("⏱️ 용해 시간 (초)", min_value=1.0, step=1.0, format="%.1f", key="dissolving_time")
            
            memo = st.text_area("📝 기타 관찰 내용 (저은 횟수, 물 온도 등)", key="memo_input")
            
            submitted = st.form_submit_button("✅ 기록 제출하기")

            if submitted:
                if dissolving_time < 1:
                    st.error("용해 시간은 1초 이상이어야 합니다.")
                else:
                    formatted_datetime = observation_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    new_data = pd.DataFrame(
                        [[formatted_datetime, condition, dissolving_time, memo]],
                        columns=["날짜 및 시간", "조건 (그룹)", "용해 시간(초)", "메모"]
                    )
                    
                    st.session_state.experiment_data = pd.concat([st.session_state.experiment_data, new_data], ignore_index=True)
                    save_data()
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ {condition}에서의 용해 시간({dissolving_time:.1f}초)이 저장되었습니다! 다른 조건이나 반복 실험을 기록해 보세요."})
                    
                    st.session_state.show_record_form = False 
                    st.rerun()

def show_results():
    """결과 그래프, 분석, 교육적 해석을 표시합니다."""
    
    df = st.session_state.experiment_data.copy()
    
    if df.empty:
        response_content = "아직 기록된 실험이 없어요. 😢 먼저 '실험 기록하기' 버튼을 눌러 시간을 기록해주세요."
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.rerun() 
        return

    # --- 데이터 전처리 및 분석 시작 ---
    try:
        # 그룹별 평균 용해 시간 계산 (챗봇의 핵심 분석 기능)
        analysis_df = df.groupby('조건 (그룹)')['용해 시간(초)'].mean().reset_index()
        analysis_df.columns = ['조건 (그룹)', '평균 용해 시간 (초)']
        analysis_df = analysis_df.set_index('조건 (그룹)').round(1)
        
        # 그래프 데이터
        chart_df = analysis_df.copy()

        # --- Educational Analysis (용해 속도 분석) ---
        
        # 두 그룹 모두 데이터가 있는지 확인
        hot_time = analysis_df.loc['🔥 뜨거운 물']['평균 용해 시간 (초)'] if '🔥 뜨거운 물' in analysis_df.index else np.nan
        cold_time = analysis_df.loc['🧊 찬 물']['평균 용해 시간 (초)'] if '🧊 찬 물' in analysis_df.index else np.nan
        
        
        if pd.isna(hot_time) or pd.isna(cold_time):
            interpretation = "정확한 비교 분석을 위해서는 **뜨거운 물**과 **찬 물** 조건 모두에서 기록이 필요합니다. ⏱️"
        else:
            if hot_time < cold_time * 0.8: # 뜨거운 물이 20% 이상 빠를 때 (정상 결과)
                time_diff = cold_time - hot_time
                
                # **5학년 교과서 개념 반영:** 용질, 용매, 용해 속도 증가 원리 설명
                interpretation = (
                    f"🎉 **용해 속도 분석 결과!** (5학년 과학 개념 적용)\n\n"
                    f"챗봇이 계산한 평균 시간은 **뜨거운 물**이 **{hot_time:.1f}초**, **찬 물**이 **{cold_time:.1f}초**로, "
                    f"뜨거운 물이 약 **{time_diff:.1f}초** 더 빨랐어요! \n\n"
                    f"이것은 물(용매)이 뜨거울수록 **물 분자의 움직임이 활발해지기** 때문이에요. 활발해진 용매 분자들이 설탕(용질)을 더 세고 빠르게 때려 **용해 속도**가 빨라진답니다. \n\n"
                    f"**⭐ 과학자처럼 생각하기!** 이번 실험에서 설탕의 양, 저어준 횟수, 입자 크기 등 **온도 외의 조건들**을 똑같이 맞췄는지 확인하는 것이 중요해요. 다른 조건이 달랐다면 정확한 결론을 내릴 수 없답니다."
                )
            elif cold_time < hot_time * 0.8: # 예상 밖의 결과
                interpretation = (
                    f"🧐 **흥미로운 결과!** 챗봇이 계산한 결과, 찬물이 뜨거운 물보다 더 빨리 녹았어요! 이 결과는 과학적 예상과 반대됩니다.\n\n"
                    f"실험 결과가 예상과 다를 때는 과학자가 되어 이유를 찾아야 해요! 혹시 **찬물의 설탕을 더 잘게 부수어 넣었거나** (입자 크기), **더 많이 저어주었나요** (저어주기)? 용해 속도에 영향을 주는 다른 요인들 때문에 이런 결과가 나올 수 있어요. 실험 조건을 다시 확인해 봅시다!"
                )
            else:
                interpretation = "두 물의 평균 용해 시간이 비슷하네요. 아마도 물의 온도 차이가 크지 않았거나, 실험 조건을 완벽하게 통제하지 못했을 수 있어요. 온도 차이를 더 크게 하거나, 다른 요인들(저어주기, 입자 크기)을 똑같이 맞추어 다시 실험해 봅시다! 🌡️"
            

    except Exception as e:
        # 데이터 처리 중 발생하는 예상치 못한 오류를 잡아 사용자에게 안내
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ **데이터 분석 중 심각한 오류가 발생했습니다.** 😭\n\n데이터 파일(`{DATA_FILE}`)의 내용이 손상되었을 수 있습니다. 오류 상세 내용: `{e}`"
        })
        st.rerun()
        return


    # --- Construct and Display Response ---
    response_content = f"📊 **실시간 용해 속도 분석 리포트**\n\n{interpretation}\n\n**✅ 챗봇 분석 요약: 평균 용해 시간**"
    
    # Append educational message and chart data to the chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_content,
        "chart_data": chart_df, # 평균 용해 시간 막대 그래프
        "dataframe": analysis_df.astype(str) # 분석 테이블
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
    if "기록" in prompt or "실험" in prompt:
        st.session_state.show_record_form = True
    elif "결과" in prompt or "보기" in prompt or "분석" in prompt:
        show_results()
    else:
        # Generic response
        response_content = "죄송해요. 😥 저는 지금 '실험 기록'과 '결과 분석'만 할 수 있어요. 둘 중 하나를 선택하거나, 아래 버튼을 눌러주세요!"
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
