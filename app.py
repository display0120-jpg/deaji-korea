import streamlit as st
import google.generativeai as genai
from PIL import Image

# 본인의 API 키를 여기에 넣으세요
MY_API_KEY = "AIzaSyCr2z0SweYhOSWzthJxNBiX-Ro3Gt9XNpI"
genai.configure(api_key=MY_API_KEY)

st.title("📚 한국사 수행평가 도우미 AI")

user_request = st.text_input("추가 요청사항", placeholder="예: 경주 관련 문화유산으로 추천해줘")
file1 = st.file_uploader("1. 수행평가 양식 사진", type=['jpg', 'png', 'jpeg'])
file2 = st.file_uploader("2. 안내문 사진", type=['jpg', 'png', 'jpeg'])

if st.button("가이드 생성"):
    if not file1 or not file2:
        st.warning("사진 2장을 모두 업로드해주세요.")
    else:
        try:
            with st.spinner("AI 분석 중..."):
                # 최신 모델명 사용 (v1beta 에러 해결용)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                img1 = Image.open(file1)
                img2 = Image.open(file2)
                
                prompt = f"""
                사진 속 수행평가 양식과 안내문을 분석해서 가이드를 작성해줘.
                요청사항: {user_request if user_request else "가장 적절한 유산 추천"}
                1. 추천 문화유산과 선정 이유.
                2. 안내문 기준에 맞춘 인터뷰 질문 및 답변 예시.
                3. 탐방 기획안 제목과 주요 포인트.
                학생이 스스로 쓸 수 있게 친절하게 방향만 알려줘.
                """
                
                response = model.generate_content([prompt, img1, img2])
                st.markdown("---")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"오류 발생: {e}")
            st.write("---")
            st.info("💡 만약 여전히 404 에러가 난다면, 터미널에서 pip install -U google-generativeai 를 다시 실행해주세요.")
