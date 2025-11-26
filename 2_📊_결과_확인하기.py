import streamlit as st
import pandas as pd

st.set_page_config(page_title="결과 확인하기", page_icon="📊")

st.markdown("# 📊 실험 결과 확인하기")
st.sidebar.header("결과 확인하기")

if 'plant_data' not in st.session_state or st.session_state.plant_data.empty:
    st.warning("아직 기록된 데이터가 없습니다. '🧪 실험 기록하기' 페이지에서 먼저 데이터를 입력해 주세요.")
else:
    st.subheader("식물 그룹별 성장 그래프")

    # 데이터 준비
    df = st.session_state.plant_data.copy()
    df['날짜'] = pd.to_datetime(df['날짜'])
    df = df.sort_values(by="날짜")

    # 피벗 테이블을 사용하여 각 그룹의 날짜별 키를 정리
    pivot_df = df.pivot_table(index='날짜', columns='그룹', values='식물 키(cm)')

    if not pivot_df.empty:
        st.line_chart(pivot_df)
        st.info(
            """
            **그래프 해석하기**
            - **X축 (가로)**: 시간이 지나는 것을 나타냅니다.
            - **Y축 (세로)**: 식물의 키(cm)를 나타냅니다.
            - **색깔별 선**: 각 식물 그룹('햇빛 드는 곳', '어두운 옷장')을 나타냅니다.

            두 그룹의 식물이 시간이 지남에 따라 어떻게 다르게 자라는지 비교해 보세요!
            """
        )
    else:
        st.info("그래프를 그리려면 데이터가 더 필요합니다. 꾸준히 관찰 결과를 기록해 주세요.")

    st.subheader("전체 기록 데이터")
    st.dataframe(st.session_state.plant_data.sort_values(by=["날짜", "그룹"]).reset_index(drop=True))