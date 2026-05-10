import streamlit as st
import google.generativeai as genai

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 위치 및 스타일
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 100px; 
        right: 20px;
        color: #999;
        font-size: 0.85em;
        font-weight: normal;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.5);
        padding: 3px 8px;
        border-radius: 5px;
    }
    .report-box {
        border: 1px solid #E6E9EF;
        border-radius: 10px;
        padding: 25px;
        background-color: #FFFFFF;
        line-height: 1.7;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 키 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

# --- 3. 모델 설정 ---
@st.cache_resource
def get_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for pref in preferences:
            if pref in available_models:
                return genai.GenerativeModel(pref)
        return genai.GenerativeModel(available_models[0])
    except:
        return None

model = get_model()

# --- 4. 수행평가 생성 함수 (중복 차단 및 억지 연결 금지 강화) ---
def generate_history_report(topic, history_list=[]):
    exclude_msg = ""
    if history_list:
        exclude_msg = f"""
        ### [필독: 중복 금지 목록] ###
        이미 학생에게 보여준 문화유산: {', '.join(history_list)}
        이 목록에 있는 유산은 절대 다시 선택하지 마세요. 반드시 '새로운' 유산을 찾아야 합니다.
        """

    prompt = f"""
    당신은 대한민국 최고의 한국사 전문가입니다. 학생의 진로/관심사인 '{topic}'와 실제로 깊고 타당한 연관이 있는 한국 문화유산(구석기~조선)을 하나 선정하세요.

    {exclude_msg}

    [작성 원칙]
    1. 억지로 끼워 맞추지 마세요. 논리적이고 역사적인 근거가 확실한 것만 선정하세요.
    2. 중복 절대 불가: 이미 추천된 유산은 제외하고 차선책 중 가장 훌륭한 유산을 고르세요.
    3. 대한민국에는 수만 개의 문화유산이 있습니다. 자격루, 거북선 같은 유명한 것 외에도 특정 분야에 특화된 유물을 폭넓게 탐색하세요.
    4. 선정 이유를 쓸 때 역사적 사실에 기반하여 누가 봐도 고개를 끄덕일 수 있는 관련성을 제시하세요.

    양식:
    1. 선정된 문화유산: 이름
    2. 선정 이유: 역사적 근거를 바탕으로 한 구체적 관련성
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

# --- 5. UI 구성 및 로직 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")
st.write("진로와 가장 관련 깊은 문화유산을 찾아 보고서 양식을 작성해 드립니다.")

# 세션 상태 관리 (새로 접속 시 초기화됨)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'report' not in st.session_state:
    st.session_state.report = ""

user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 건축가, 생명공학, 로봇공학 등")

col1, col2 = st.columns(2)

# [보고서 생성]
if col1.button("보고서 생성"):
    if user_input:
        with st.spinner("가장 적절한 문화유산을 탐색 중입니다..."):
            st.session_state.history = [] 
            res = generate_history_report(user_input)
            st.session_state.report = res
            try:
                name = res.split('1. 선정된 문화유산:')[1].split('\n')[0].strip()
                st.session_state.history = [name]
            except:
                pass
    else:
        st.warning("분야를 입력해주세요.")

# [다른 유산 추천]
if col2.button("다른 유산 추천 🔄"):
    if user_input and st.session_state.history:
        with st.spinner(f"새로운 관련 유산을 찾는 중..."):
            res = generate_history_report(user_input, st.session_state.history)
            st.session_state.report = res
            try:
                name = res.split('1. 선정된 문화유산:')[1].split('\n')[0].strip()
                st.session_state.history.append(name)
            except:
                pass
    elif not user_input:
        st.warning("분야를 먼저 입력해주세요.")
    else:
        st.info("'보고서 생성'을 먼저 눌러주세요.")

# --- 6. 결과 출력 ---
if st.session_state.report:
    st.divider()
    st.markdown('<div class="report-box">', unsafe_allow_html=True)
    st.markdown(st.session_state.report)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 다운로드 버튼
    st.download_button(
        label="📄 결과 저장 (TXT)",
        data=f"국사쌤 사랑합니다 ❤️\n\n{st.session_state.report}",
        file_name="report.txt"
    )
