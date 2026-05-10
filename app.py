import streamlit as st
import google.generativeai as genai

# --- 1. 페이지 설정 및 디자인 (CSS 추가) ---
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 우측 상단 문구 및 보고서 디자인 스타일
st.markdown("""
    <style>
    .teacher-love {
        text-align: right;
        color: #FF4B4B;
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: -10px;
    }
    .report-box {
        border: 1px solid #E6E9EF;
        border-radius: 10px;
        padding: 25px;
        background-color: #F8F9FB;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API 키 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

# --- 3. 모델 자동 검색 로직 ---
@st.cache_resource
def get_best_available_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for pref in preferences:
            if pref in available_models:
                m = genai.GenerativeModel(pref)
                m.generate_content("test", generation_config={"max_output_tokens": 1})
                return m, pref
        if available_models:
            m = genai.GenerativeModel(available_models[0])
            return m, available_models[0]
        return None, "사용 가능한 모델이 목록에 없습니다."
    except Exception as e:
        return None, str(e)

model, model_name = get_best_available_model()

if model is None:
    st.error("🚨 모델 연결 실패")
    st.code(f"에러 내용: {model_name}")
    st.stop()

# --- 4. 수행평가 생성 함수 ---
def generate_history_report(topic, history_list=[]):
    exclude = f"(이미 나온 {', '.join(history_list)} 제외)" if history_list else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생의 진로/관심사 '{topic}'와 관련된 한국 문화유산(구석기~조선) 수행평가 보고서를 작성하세요. {exclude}
    반드시 다음 양식을 지켜주세요:
    1. 선정된 문화유산: 이름
    2. 선정 이유: 진로와 연결된 이유
    3. 제작 시대: 시대
    4. 현재 위치: 소재지
    5. 인터뷰 1(생활/정치): Q&A
    6. 인터뷰 2(시련/변화): Q&A
    7. 인터뷰 3(비판/융합/비교 중 택1): 관점 명시 후 Q&A
    8. 테마 탐방안: 제목과 포인트 3가지
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"생성 실패: {str(e)}"

# --- 5. UI 구성 ---
st.title("🏛️ 한국사 수행평가 AI")
st.success(f"✅ AI 모델 연결 성공! ({model_name})")

if 'history' not in st.session_state: st.session_state.history = []
if 'report' not in st.session_state: st.session_state.report = ""

# 입력창
user_input = st.text_input("나의 진로나 관심분야를 적어주세요")

c1, c2 = st.columns(2)
if c1.button("보고서 생성"):
    if user_input:
        with st.spinner("AI가 내용을 작성 중입니다..."):
            res = generate_history_report(user_input)
            st.session_state.report = res
            st.session_state.history = [res.split('\n')[0]]
    else: st.warning("진로를 먼저 입력해주세요.")

if c2.button("다른 거 추천 🔄"):
    if user_input:
        with st.spinner("새로운 유산을 찾는 중..."):
            res = generate_history_report(user_input, st.session_state.history)
            st.session_state.report = res
            st.session_state.history.append(res.split('\n')[0])

# --- 6. 결과 출력 (사랑합니다 문구 포함) ---
if st.session_state.report:
    st.divider()
    
    # 우측 상단 문구 출력
    st.markdown('<div class="teacher-love">국사쌤 사랑합니다 ❤️</div>', unsafe_allow_html=True)
    
    # 보고서 내용 출력 (박스 안에 넣기)
    st.markdown('<div class="report-box">', unsafe_allow_html=True)
    st.markdown(st.session_state.report)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 다운로드 버튼 (저장 파일에도 문구 추가)
    final_text = f"국사쌤 사랑합니다 ❤️\n\n{st.session_state.report}"
    st.download_button("결과 저장 (TXT)", final_text, file_name="report.txt")
