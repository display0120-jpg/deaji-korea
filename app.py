import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="한국사 수행평가 도우미")

# API 키 설정 (GitHub에 올릴 때는 보안을 위해 입력창으로 만듭니다)
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("왼쪽 사이드바에 API 키를 입력해야 작동합니다.")

st.title("📚 한국사 수행평가 도우미 AI")
user_request = st.text_input("추가 요청사항", placeholder="예: 경주 관련 문화유산으로 추천해줘")

col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. 수행평가 양식 사진", type=['jpg', 'png', 'jpeg'])
with col2:
    file2 = st.file_uploader("2. 안내문 사진", type=['jpg', 'png', 'jpeg'])

if st.button("가이드 생성"):
    if not api_key:
        st.error("API 키가 없습니다.")
    elif not file1 or not file2:
        st.warning("사진 2장을 모두 업로드해주세요.")
    else:
        try:
            with st.spinner("AI 분석 중..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                img1 = Image.open(file1)
                img2 = Image.open(file2)
                prompt = f"""
                사진 속 수행평가 양식과 안내문을 분석해서 가이드를 작성해줘.
                학생 요청사항: {user_request if user_request else "가장 적절한 유산 추천"}
                1. 추천 문화유산과 선정 이유.
                2. 안내문 기준에 맞춘 인터뷰 질문 및 답변 예시.
                3. 탐방 기획안 제목과 주요 포인트.
                학생이 스스로 쓸 수 있게 방향만 친절하게 알려줘.
                """
                response = model.generate_content([prompt, img1, img2])
                st.markdown("---")
                st.markdown(response.text)
        except Exception as e:
            st.error(f"오류: {e}")