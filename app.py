import streamlit as st
import pandas as pd
import numpy as np

st.title("Simple Echo Chatbot")

# 세션 상태(session_state)에 메시지 기록을 초기화합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용을 화면에 표시합니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자로부터 입력을 받습니다.
if prompt := st.chat_input("무엇이든 물어보세요."):
    # 사용자 메시지를 컨테이너에 표시하고 기록에 추가합니다.
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 챗봇의 응답을 생성합니다. (여기서는 사용자의 입력을 그대로 따라합니다)
    response = f"Echo: {prompt}"
    
    # 챗봇 응답을 컨테이너에 표시하고 기록에 추가합니다.
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})