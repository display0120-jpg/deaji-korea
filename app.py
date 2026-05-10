import streamlit as st
import google.generativeai as genai

# --- 1. 페이지 설정 및 API 연결 ---
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit 설정(Secrets)에서 API 키를 등록해야 합니다.")
    st.stop()

# API 키의 공백이나 따옴표 제거 후 설정
api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '').replace("'", "")
genai.configure(api_key=api_key)

# 가장 안정적인 모델 연결 시도
@st.cache_resource
def load_model():
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("Hi", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = load_model()

# --- 2. 수행평가 내용 생성 함수 ---
def generate_report(interest, history=[]):
    exclude_text = f"(단, {', '.join(history)}는 이미 추천했으니 제외)" if history else ""
    
    prompt = f"""
    당신은 고등학교 역사 교사입니다. 학생의 진로/관심사 '{interest}'와 관련된 한국 문화유산(구석기~조선)을 선정해 수행평가를 작성하세요.
    {exclude_text}

    반드시 아래 양식을 엄격히 지켜주세요:
    1. 선정된 문화유산: [이름]
    2. 선정 이유: [진로/관심사와 유산의 특징을 아주 구체적으로 연결하여 작성]
    3. 제작 시대: [시대명]
    4. 현재 위치(소재지): [정확한 주소]

    [인터뷰 1 - 과거인들의 생활, 사상, 정치]
    Q: [문화유산의 특징과 당시 시대상을 묻는 질문]
    A: [유산의 배경, 종교적/정치적 의미를 담은 답변]

    [인터뷰 2 - 역사적 시련과 변화]
    Q: [세월을 거치며 겪은 시련이나 복원 과정, 혹은 현재 상황 질문]
    A: [전쟁, 파손, 복원 노력 또는 현재의 보존 현황 답변]

    [인터뷰 3 - 심화 관점(비판적/융합적/비교사적 중 택1)]
    *선택한 관점 종류를 제목에 명시할 것*
    Q: [문제의식이 담긴 날카로운 질문이나 타 교과 연계 질문]
    A: [깊이 있는 통찰이 담긴 답변]

    [선정한 문화유산 테마 탐방안]
    - 기획 의도가 포함된 제목: [흥미로운 제목]
    - 필수 관람 포인트(감상법): [문장으로 완성된 3가지 핵심 포인트]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"내용 생성 중 에러 발생: {e}"

# --- 3. UI 구성 ---
st.title("🏛️ 한국사 수행평가: 문화유산 탐구 AI")
st.info("진로를 입력하면 수행평가 양식에 맞춘 인터뷰와 탐방안을 써드립니다.")

if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""

with st.sidebar:
    user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 인공지능, 건축가, 의학...")
    c1, c2 = st.columns(2)
    submit = c1.button("내용 생성")
    retry = c2.button("다른 유산 🔄")

if (submit or retry) and user_input:
    with st.spinner("AI가 자료를 조사 중입니다..."):
        # 다른 유산 추천 시 히스토리 전달
        h_list = st.session_state.history if retry else []
        res = generate_report(user_input, h_list)
        st.session_state.current_text = res
        
        # 유산 이름 추출하여 기록
        try:
            name = res.split('\n')[0].split(':')[-1].strip()
            if retry:
                st.session_state.history.append(name)
            else:
                st.session_state.history = [name]
        except:
            pass

if st.session_state.current_text:
    st.markdown("---")
    st.markdown(st.session_state.current_text)
    st.download_button("결과를 파일로 저장", st.session_state.current_text, file_name="history_task.txt")
