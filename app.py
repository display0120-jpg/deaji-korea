import streamlit as st
import google.generativeai as genai

# 웹페이지 설정
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# --- 1. API 연결 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 작동 가능한 모델 자동 찾기 (404 에러 방지) ---
@st.cache_resource
def load_working_model():
    # 시도해볼 모델 명칭 후보들
    model_candidates = [
        'gemini-1.5-flash',
        'models/gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    for name in model_candidates:
        try:
            m = genai.GenerativeModel(name)
            # 모델이 응답하는지 아주 짧게 테스트
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except Exception:
            continue
    return None

model = load_working_model()

if model is None:
    st.error("❌ 현재 API 키로 사용 가능한 Gemini 모델을 찾을 수 없습니다.")
    st.info("해결 방법: Google AI Studio에서 새로운 API 키를 발급받아 Secrets에 다시 등록해 보세요.")
    st.stop()

# --- 3. 수행평가 생성 로직 ---
def generate_report(interest, history=[]):
    exclude = f"(단, {', '.join(history)}는 이미 추천했으니 제외)" if history else ""
    
    prompt = f"""
    당신은 고등학교 역사 교사입니다. 학생의 진로/관심사 '{interest}'와 관련된 한국 문화유산(구석기~조선)을 선정해 수행평가를 작성하세요.
    {exclude}

    반드시 아래 양식을 엄격히 지켜주세요:
    1. 선정된 문화유산: 이름
    2. 선정 이유: 진로와 연결된 상세 이유
    3. 제작 시대: 시대명
    4. 현재 위치: 소재지 주소
    5. 인터뷰 1(생활/사상/정치): Q&A 형식
    6. 인터뷰 2(시련/변화/현황): Q&A 형식
    7. 인터뷰 3(비판/융합/비교 중 택1): 관점 명시 후 Q&A 형식
    8. 테마 탐방안: 제목 및 필수 포인트 3가지(문장으로 완성)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"내용 생성 중 에러 발생: {e}"

# --- 4. UI 구성 ---
st.title("🏛️ 한국사 수행평가 도우미 AI")
st.success(f"✅ 모델 연결 성공: {model.model_name}")

if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""

user_input = st.text_input("나의 진로 또는 관심분야를 입력하세요", placeholder="예: 생명공학, 건축가, IT 보안...")

col1, col2 = st.columns(2)
with col1:
    if st.button("수행평가 내용 생성"):
        if user_input:
            with st.spinner("AI가 자료를 조사하여 작성 중입니다..."):
                res = generate_report(user_input)
                st.session_state.current_text = res
                name = res.split('\n')[0]
                st.session_state.history = [name]
        else:
            st.warning("관심분야를 입력해주세요.")

with col2:
    if st.button("다른 문화유산 추천받기 🔄"):
        if user_input:
            with st.spinner("다른 유산을 찾는 중..."):
                res = generate_report(user_input, st.session_state.history)
                st.session_state.current_text = res
                st.session_state.history.append(res.split('\n')[0])
        else:
            st.warning("관심분야를 입력해주세요.")

if st.session_state.current_text:
    st.markdown("---")
    st.markdown(st.session_state.current_text)
    st.download_button("결과를 텍스트 파일로 저장", st.session_state.current_text, file_name="history_report.txt")
