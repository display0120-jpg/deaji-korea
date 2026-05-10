import streamlit as st
import google.generativeai as genai

# --- 1. API 키 및 모델 설정 ---
# Streamlit Secrets에서 API 키를 가져옵니다. 
# (에러 방지를 위해 키가 없을 때의 안내 문구 추가)
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("설정(Secrets)에 GOOGLE_API_KEY가 등록되지 않았습니다. Streamlit 대시보드에서 등록해 주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 가장 안정적인 gemini-1.5-flash 모델을 사용합니다.
model = genai.GenerativeModel('gemini-1.5-flash')

# 웹페이지 설정
st.set_page_config(page_title="한국사 수행평가 도우미", page_icon="📜", layout="wide")

# --- 2. 프롬프트 생성 함수 (수행평가 양식 반영) ---
def generate_heritage_report(user_interest, exclude_list=[]):
    exclude_text = ""
    if exclude_list:
        exclude_text = f"단, 다음 문화유산은 이미 추천했으니 제외해줘: {', '.join(exclude_list)}"

    prompt = f"""
    당신은 고등학교 역사 교사이자 전문가입니다. 
    학생의 진로/관심분야인 '{user_interest}'와 관련이 깊은 한국 문화유산(구석기~조선시대 사이)을 하나 선정하여 수행평가 보고서를 작성해 주세요.
    {exclude_text}

    다음 형식과 내용을 반드시 지켜서 작성하세요:

    1. 선정된 문화유산: [문화유산 이름]
    2. 선정 이유: [학생의 진로/관심사와 유산의 특징을 아주 구체적으로 연결하여 작성]
    3. 제작 시대: [예: 조선 시대]
    4. 현재 위치(소재지): [예: 경상북도 경주시]

    [인터뷰 1 - 과거인들의 생활, 사상, 정치]
    Q: [문화유산의 특징과 당시 시대상을 묻는 질문]
    A: [유산이 만들어진 배경, 종교적/정치적 의미 등을 포함한 상세한 답변]

    [인터뷰 2 - 역사적 시련과 변화]
    Q: [세월을 거치며 겪은 시련이나 복원 과정, 혹은 현재 상황에 대한 질문]
    A: [전쟁, 파손, 복원 노력 또는 현재의 보존 현황에 대한 답변]

    [인터뷰 3 - 심화 관점(비판적, 융합적, 비교사적 중 택1)]
    *반드시 비판적/융합적/비교사적 관점 중 하나를 선택하고 제목에 표시할 것*
    Q: [날카로운 질문이나 타 교과와 연계된 질문]
    A: [깊이 있는 통찰이 담긴 답변]

    [선정한 문화유산 테마 탐방안]
    - 기획 의도가 포함된 제목: [흥미로운 탐방 제목]
    - 필수 관람 포인트(감상법): [문장으로 완성된 3가지 핵심 포인트]
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- 3. UI 구성 ---
st.title("🏛️ 한국사 수행평가: 문화유산 탐구 글쓰기")
st.write("진로와 관심분야를 입력하면 나만의 문화유산 가상 인터뷰를 만들어 드립니다.")

# 세션 상태 초기화 (이전 결과 저장용)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = ""

# 사이드바 입력창
with st.sidebar:
    st.header("입력창")
    user_input = st.text_input("나의 진로/관심분야", placeholder="예: 의학, 디자인, 컴퓨터 공학...")
    
    col1, col2 = st.columns(2)
    with col1:
        submit = st.button("내용 생성")
    with col2:
        retry = st.button("다른 유산 찾기 🔄")

# 메인 로직
if submit:
    if user_input:
        with st.spinner("AI 선생님이 내용을 구성하고 있습니다..."):
            report = generate_heritage_report(user_input)
            st.session_state.current_report = report
            # 문화유산 이름 추출 (첫 줄)
            name = report.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
            st.session_state.history = [name]
    else:
        st.warning("먼저 관심분야를 입력해 주세요.")

if retry:
    if user_input:
        with st.spinner("다른 문화유산을 분석 중입니다..."):
            report = generate_heritage_report(user_input, st.session_state.history)
            st.session_state.current_report = report
            name = report.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
            st.session_state.history.append(name)
    else:
        st.warning("먼저 관심분야를 입력해 주세요.")

# 결과 화면
if st.session_state.current_report:
    st.markdown("---")
    st.markdown(st.session_state.current_report)
    
    # 다운로드 버튼
    st.download_button(
        label="📄 결과 복사/저장 (TXT)",
        data=st.session_state.current_report,
        file_name=f"한국사_수행평가_{user_input}.txt",
        mime="text/plain"
    )
