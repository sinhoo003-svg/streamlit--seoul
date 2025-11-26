import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="신나는 초등 과학 실험실",
    page_icon="🔬",
)

st.title("🔬 과학 실험 챗봇")

# --- 데이터 관리 함수 ---
DATA_FILE = "plant_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["날짜", "그룹", "식물 키(cm)", "메모"])

def save_data():
    if 'plant_data' in st.session_state:
        st.session_state.plant_data.to_csv(DATA_FILE, index=False)

# --- 세션 상태 초기화 ---
if 'plant_data' not in st.session_state:
    st.session_state.plant_data = load_data()
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요? 아래에서 '실험 기록' 또는 '결과 보기'를 선택해주세요."}
    ]

# --- 이전 대화 내용 표시 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "dataframe" in message:
            st.dataframe(message["dataframe"])
        if "chart" in message:
            st.line_chart(message["chart"])

# --- 챗봇의 기능 정의 ---
def show_record_form():
    """데이터 기록 폼을 표시하는 함수"""
    with st.chat_message("assistant"):
        st.write("🌿 식물 성장 관찰일지를 기록합니다.")
        with st.form("data_form"):
            observation_date = st.date_input("관찰 날짜", value=datetime.now())
            plant_group = st.selectbox("식물 그룹 선택", ("☀️ 햇빛 드는 곳", "🌑 어두운 옷장"))
            plant_height = st.number_input("식물의 키 (cm)", min_value=0.0, format="%.1f")
            memo = st.text_area("기타 관찰 내용 (선택 사항)")
            submitted = st.form_submit_button("기록 제출하기")

            if submitted:
                formatted_date = observation_date.strftime("%Y-%m-%d")
                new_data = pd.DataFrame(
                    [[formatted_date, plant_group, plant_height, memo]],
                    columns=["날짜", "그룹", "식물 키(cm)", "메모"]
                )
                st.session_state.plant_data = pd.concat([st.session_state.plant_data, new_data], ignore_index=True)
                save_data()
                st.success("✅ 데이터가 성공적으로 기록되었습니다!")
                st.rerun() # 폼을 사라지게 하고 화면을 새로고침

def show_results():
    """결과 그래프와 데이터를 표시하는 함수"""
    with st.chat_message("assistant"):
        if st.session_state.plant_data.empty:
            st.warning("아직 기록된 데이터가 없습니다. 먼저 실험을 기록해주세요.")
            return

        st.write("📊 실험 결과를 보여드릴게요.")
        
        # 데이터 준비
        df = st.session_state.plant_data.copy()
        df['날짜'] = pd.to_datetime(df['날짜'])
        df = df.sort_values(by="날짜")
        pivot_df = df.pivot_table(index='날짜', columns='그룹', values='식물 키(cm)')

        # 그래프와 데이터프레임을 메시지에 추가하여 표시
        st.line_chart(pivot_df)
        st.dataframe(df.reset_index(drop=True))

# --- 사용자 입력 처리 ---
if prompt := st.chat_input("무엇을 하시겠어요?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 사용자의 입력에 따라 기능 실행
    if "기록" in prompt:
        show_record_form()
    elif "결과" in prompt or "보기" in prompt:
        show_results()
    else:
        with st.chat_message("assistant"):
            st.write("죄송해요, 잘 이해하지 못했어요. '실험 기록' 또는 '결과 보기' 중에서 선택해주세요.")

# --- 초기 화면에 버튼 표시 ---
if len(st.session_state.messages) == 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 실험 기록하기"):
            st.session_state.messages.append({"role": "user", "content": "실험 기록하기"})
            show_record_form()
    with col2:
        if st.button("📈 결과 보기"):
            st.session_state.messages.append({"role": "user", "content": "결과 보기"})
            show_results()