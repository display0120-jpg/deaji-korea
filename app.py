import streamlit as st
import google.generativeai as genai

# 웹페이지 기본 설정
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 1. API 키 설정
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요!")
    st.stop()

# 2. 모델 설정 (가장 안정적인 모델명 사용)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"모델 로드 실패: {e}")
    st.stop()

# 3. 데이터 저장용 세션 상태 초기화
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_content' not in st.session_state:
    st.session_state.current_content = ""

# 4. 프롬프트 생성 함수
def get_ai_response(user_job, excludes=[]):
    exclude_msg = f"(이전에 추천된 {', '.join(excludes)}는 제외할 것)" if excludes else ""
    
    prompt = f"""
    당신은 고등학교 역사 선생님입니다. 학생의 진로/관심사 '{user_job}'와 관련된 한국 문화유산(구석기~조선시대) 하나를 골라 수행평가를 완성하세요.
    {exclude_msg}

    다음 양식을 100% 지켜주세요:
    
    1. 선정된 문화유산: [이름]
    2. 선정 이유: [관심사와 유산의 특징을 구체적으로 연결]
    3. 제작 시대: [예: 조선시대]
    4. 현재 위치: [소재지]

    [인터뷰 1 - 생활/정치]
    Q: [질문]
    A: [답변]

    [인터뷰 2 - 시련/변화]
    Q: [질문]
    A: [답변]

    [인터뷰 3 - 심화 관점(비판/융합/비교 중 택1)]
    *선택한 관점 명시*
    Q: [질문]
    A: [답변]

    [테마 탐방안]
    - 제목: [기획 의도가 담긴 제목]
    - 필수 관람 포인트: [3가지 문장으로]
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"에러 발생: {str(e)}"

# 5. UI 화면
st.title("🏛️ 한국사 수행평가 도우미")
st.info("진로를 입력하면 수행평가 양식에 맞춰 내용을 써줍니다.")

user_input = st.text_input("나의 진로/관심분야 (예: 건축, 인공지능, 의학)")

col1, col2 = st.columns(2)
with col1:
    if st.button("내용 생성하기"):
        if user_input:
            with st.spinner("AI가 분석 중..."):
                result = get_ai_response(user_input)
                st.session_state.current_content = result
                # 문화유산 이름만 추출해서 기록
                name = result.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
                st.session_state.history = [name]
        else:
            st.warning("진로를 먼저 입력하세요.")

with col2:
    if st.button("다른 유산 추천받기 🔄"):
        if user_input:
            with st.spinner("새로운 유산 찾는 중..."):
                result = get_ai_response(user_input, st.session_state.history)
                st.session_state.current_content = result
                name = result.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
                st.session_state.history.append(name)
        else:
            st.warning("진로를 먼저 입력하세요.")

# 결과 출력
if st.session_state.current_content:
    st.divider()
    st.markdown(st.session_state.current_content)
    st.download_button("결과 파일 다운로드", st.session_state.current_content, file_name="history_report.txt")
