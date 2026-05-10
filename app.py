import streamlit as st
import google.generativeai as genai

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 우측 상단 "국사쌤 사랑합니다" 스타일 적용
st.markdown("""
    <style>
    .teacher-love {
        text-align: right;
        color: #ff4b4b;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: -20px;
    }
    .report-container {
        border: 2px solid #f0f2f6;
        padding: 30px;
        border-radius: 10px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. API 및 모델 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def load_model():
    # 사용 가능한 모델을 자동으로 찾습니다.
    model_candidates = ['gemini-1.5-flash', 'gemini-pro']
    for name in model_candidates:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = load_model()

if model is None:
    st.error("❌ AI 모델 연결에 실패했습니다. API 키를 확인해주세요.")
    st.stop()

# --- 3. 수행평가 생성 로직 ---
def generate_report(interest, history=[]):
    exclude = f"(단, {', '.join(history)}는 이미 추천했으니 제외)" if history else ""
    
    prompt = f"""
    당신은 고등학교 한국사 선생님입니다. 학생의 진로/관심분야인 '{interest}'와 깊이 연관된 한국 문화유산(구석기~조선)을 선정하여 수행평가 보고서를 작성해 주세요.
    {exclude}

    다음 양식을 엄격히 지켜서 작성하세요:
    
    1. 선정된 문화유산: [이름]
    2. 선정 이유: [진로/관심사와 유산의 특징을 아주 구체적으로 연결하여 작성]
    3. 제작 시대: [예: 조선시대]
    4. 현재 위치(소재지): [예: 경상북도 경주시]

    [인터뷰 1 - 과거인의 생활, 사상, 정치]
    Q: [문화유산의 특징과 당시 시대상을 묻는 질문]
    A: [시대적 배경과 의미를 담은 상세한 답변]

    [인터뷰 2 - 역사적 시련과 변화]
    Q: [세월을 거치며 겪은 시련이나 현재 상황을 묻는 질문]
    A: [전쟁, 파손, 복원 또는 현재의 보존 현황 답변]

    [인터뷰 3 - 심화 관점(비판적, 융합적, 비교사적 중 택1)]
    *반드시 관점 종류를 제목에 명시할 것*
    Q: [날카로운 질문 또는 타 교과 연계 질문]
    A: [통찰력 있는 답변]

    [선정한 문화유산 테마 탐방안]
    - 기획 의도가 포함된 제목: [흥미로운 제목]
    - 필수 관람 포인트(감상법): [문장으로 완성된 3가지 핵심 포인트]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"내용 생성 중 오류 발생: {e}"

# --- 4. 메인 UI ---
st.title("🏛️ 한국사 문화유산 탐구 수행평가 도우미")

if 'history' not in st.session_state: st.session_state.history = []
if 'report' not in st.session_state: st.session_state.report = ""

# 사이드바 입력창
with st.sidebar:
    st.header("입력창")
    user_input = st.text_input("나의 진로/관심분야", placeholder="예: 인공지능, 간호학, 건축...")
    c1, c2 = st.columns(2)
    if c1.button("보고서 작성"):
        if user_input:
            with st.spinner("AI 선생님이 자료를 조사 중입니다..."):
                res = generate_report(user_input)
                st.session_state.report = res
                name = res.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
                st.session_state.history = [name]
        else: st.warning("진로를 입력해주세요.")
    
    if c2.button("다른 유산 추천 🔄"):
        if user_input:
            with st.spinner("새로운 유산을 찾는 중..."):
                res = generate_report(user_input, st.session_state.history)
                st.session_state.report = res
                name = res.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
                st.session_state.history.append(name)
        else: st.warning("진로를 입력해주세요.")

# --- 5. 결과 출력 영역 ---
if st.session_state.report:
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    
    # 우측 상단 문구 추가
    st.markdown('<p class="teacher-love">국사쌤 사랑합니다 ❤️</p>', unsafe_allow_html=True)
    
    st.markdown("### 📜 문화유산 탐구 보고서")
    st.markdown("---")
    st.markdown(st.session_state.report)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 다운로드 버튼
    st.download_button(
        label="📄 보고서 파일로 저장하기",
        data=f"국사쌤 사랑합니다 ❤️\n\n{st.session_state.report}",
        file_name="한국사_수행평가_보고서.txt",
        mime="text/plain"
    )
else:
    st.info("왼쪽 사이드바에 진로를 입력하고 '보고서 작성' 버튼을 눌러주세요!")
