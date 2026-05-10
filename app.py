import streamlit as st
import google.generativeai as genai

# --- 설정 ---
# ⚠️ 여기에 발급받은 본인의 API 키를 입력하세요.
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# --- 프롬프트 생성 함수 ---
def generate_heritage_report(user_interest, exclude_list=[]):
    exclude_str = f"이미 추천된 다음 문화유산은 제외해줘: {', '.join(exclude_list)}" if exclude_list else ""
    
    prompt = f"""
    당신은 고등학교 한국사 선생님이자 역사 전문가입니다. 
    사용자의 진로/관심분야인 '{user_interest}'와 관련하여 구석기 시대부터 조선 시대까지의 한국 문화유산 중 하나를 선정해 수행평가 답변을 작성해주세요.
    {exclude_str}

    다음 양식을 엄격히 지켜서 한국어로 답변하세요:

    1. 선정된 문화유산: [이름]
    2. 선정 이유: [사용자의 진로/관심사와 연결하여 구체적으로 작성]
    3. 제작 시대: [예시: 조선시대]
    4. 현재 위치(소재지): [예시: 서울특별시 종로구]

    5. 인터뷰 1 (생활/사상/정치):
       Q: [문화유산의 특징을 묻는 질문]
       A: [과거 사람들의 생활 모습, 사상, 정치 등과 연결된 답변]

    6. 인터뷰 2 (시련/변화/현황):
       Q: [세월을 거치며 겪은 역사적 시련이나 현재 상황을 묻는 질문]
       A: [전쟁, 소실, 복원 과정 또는 현재의 모습에 대한 답변]

    7. 인터뷰 3 (비판적/융합적/비교사적 관점 중 하나 선택):
       *선택한 관점 종류를 명시할 것*
       Q: [문제의식이 담긴 날카로운 질문]
       A: [깊이 있는 통찰이 담긴 답변]

    8. 테마 탐방안:
       - 기획 의도가 포함된 제목: [흥미로운 제목]
       - 필수 관람 포인트(감상법): [문장으로 완성된 2~3가지 포인트]
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- UI 부분 ---
st.title("🏛️ 문화유산 탐구 글쓰기 AI 도우미")
st.info("진로와 관심분야를 입력하면 수행평가 양식에 맞춰 내용을 구성해 드립니다.")

# 세션 상태 초기화 (결과 저장용)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = ""

with st.sidebar:
    user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 컴퓨터 공학, 건축, 의학, 미술 등")
    submit_btn = st.button("추천 및 내용 생성")
    
    if st.button("다른 문화유산 알려줘! 🔄"):
        if user_input:
            with st.spinner("새로운 문화유산을 찾고 있습니다..."):
                new_report = generate_heritage_report(user_input, st.session_state.history)
                # 문화유산 이름만 추출해서 히스토리에 추가 (간단하게 첫 줄에서 추출)
                first_line = new_report.split('\n')[0]
                st.session_state.history.append(first_line)
                st.session_state.current_report = new_report
        else:
            st.warning("먼저 관심분야를 입력해주세요.")

# 메인 화면 결과 출력
if submit_btn:
    if user_input:
        with st.spinner("AI가 수행평가 내용을 작성 중입니다..."):
            report = generate_heritage_report(user_input)
            st.session_state.current_report = report
            # 중복 방지를 위해 기록
            first_line = report.split('\n')[0]
            st.session_state.history = [first_line]
    else:
        st.warning("관심분야를 입력해 주세요!")

if st.session_state.current_report:
    st.divider()
    st.markdown(st.session_state.current_report)
    
    st.download_button(
        label="텍스트 파일로 저장하기",
        data=st.session_state.current_report,
        file_name="한국사_수행평가_초안.txt",
        mime="text/plain"
    )
