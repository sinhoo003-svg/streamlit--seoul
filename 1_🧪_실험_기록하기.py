import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="실험 기록하기", page_icon="🧪")

st.markdown("# 🌿 식물 성장 관찰일지 기록하기")
st.sidebar.header("실험 기록하기")

# 세션 상태에 데이터프레임 초기화
if 'plant_data' not in st.session_state:
    st.session_state.plant_data = pd.DataFrame(columns=["날짜", "그룹", "식물 키(cm)", "메모"])

st.subheader("오늘의 관찰 결과 입력")

with st.form("data_form", clear_on_submit=True):
    observation_date = st.date_input("관찰 날짜", value=datetime.now())
    plant_group = st.selectbox("식물 그룹 선택", ("☀️ 햇빛 드는 곳", "🌑 어두운 옷장"))
    plant_height = st.number_input("식물의 키 (cm)", min_value=0.0, format="%.1f")
    memo = st.text_area("기타 관찰 내용 (선택 사항)")

    submitted = st.form_submit_button("기록 제출하기")

    if submitted:
        # 날짜 포맷 변경
        formatted_date = observation_date.strftime("%Y-%m-%d")

        new_data = pd.DataFrame(
            [[formatted_date, plant_group, plant_height, memo]],
            columns=["날짜", "그룹", "식물 키(cm)", "메모"]
        )
        st.session_state.plant_data = pd.concat([st.session_state.plant_data, new_data], ignore_index=True)
        st.success("데이터가 성공적으로 기록되었습니다!")

st.subheader("전체 기록 데이터")

if not st.session_state.plant_data.empty:
    # 날짜 기준으로 정렬
    display_data = st.session_state.plant_data.sort_values(by=["날짜", "그룹"]).reset_index(drop=True)
    st.dataframe(display_data)
else:
    st.warning("아직 기록된 데이터가 없습니다. 위에서 첫 관찰 결과를 입력해 주세요.")