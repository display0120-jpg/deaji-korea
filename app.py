import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 1. API 키 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

# 2. 모델 연결 (최신 1.5-flash 모델 사용)
@st.cache_resource
def load_gemini_model():
    # 가장 에러가 적은 최신 모델 명칭입니다.
    model_name = 'gemini-1.5-flash' 
    try:
        m = genai.GenerativeModel(model_name)
        # 연결 테스트
        m.generate_content("test", generation_config={"max_output_tokens": 1})
        return m, None
    except Exception as e:
        return None, str(e)

model, error_msg = load_gemini_model()

if model is None:
    st.error("🚨 모델 연결 실패")
    st.code(f"에러 내용: {error_msg}")
    st.info("해결법: API 키를 새로 발급받거나, 잠시 후 다시 시도해보세요.")
    st.stop()

# 3. 수행평가 생성 로직 (이미지 양식 반영)
def create_assignment(topic, history_list=[]):
    exclude = f"(이미 추천된 {', '.join(history_list)}는 제외)" if history_list else ""
    
    prompt = f"""
    당신은 고등학교 한국사 교사입니다. 학생의 진로/관심사 '{topic}'와 연관된 한국 문화유산(구석기~조선) 중 하나를 선정하여 수행평가 보고서를 작성하세요.
    {exclude}

    반드시 다음 양식을 엄격히 지켜서 한국어로 작성하세요:

    1. 선정된 문화유산: [이름]
    2. 선정 이유: [진로/관심사와 유산의 특징을 아주 구체적으로 연결하여 작성]
    3. 제작 시대: [예: 조선시대]
    4. 현재 위치(소재지): [예: 경기도 수원시]

    [인터뷰 1 - 과거인의 생활, 사상, 정치]
    Q: [문화유산의 특징과 당시 시대상을 묻는 질문]
    A: [시대적 배경과 의미를 담은 상세한 답변]

    [인터뷰 2 - 역사적 시련과 변화]
    Q: [세월을 거치며 겪은 시련이나 현재 상황을 묻는 질문]
    A: [전쟁, 파손, 복원 또는 현재의 보존 현황 답변]

    [인터뷰 3 - 심화 관점(비판적, 융합적, 비교사적 중 택1)]
    *반드시 관점 종류를 제목에 쓰고 깊이 있게 답변할 것*
    Q: [날카로운 질문 또는 타 교과 융합 질문]
    A: [통찰력 있는 답변]

    [선정한 문화유산 테마 탐방안]
    - 기획 제목: [흥미로운 제목]
    - 필수 관람 포인트: [문장으로 완성된 3가지 핵심 포인트]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"생성 중 오류 발생: {str(e)}"

# 4. UI 구성
st.title("🏛️ 한국사 수행평가 AI 도우미")
st.success(f"✅ AI 연결 성공 (모델: {model.model_name})")

if 'history' not in st.session_state: st.session_state.history = []
if 'report' not in st.session_state: st.session_state.report = ""

user_input = st.text_input("본인의 진로나 관심분야를 적어주세요 (예: 생명공학, 건축, 디자인)")

c1, c2 = st.columns(2)
if c1.button("보고서 생성"):
    if user_input:
        with st.spinner("내용을 구성하고 있습니다..."):
            res = create_assignment(user_input)
            st.session_state.report = res
            # 이름 추출 시도
            name = res.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
            st.session_state.history = [name]
    else: st.warning("진로를 먼저 입력해주세요.")

if c2.button("다른 유산 추천 🔄"):
    if user_input:
        with st.spinner("다른 유산을 찾는 중..."):
            res = create_assignment(user_input, st.session_state.history)
            st.session_state.report = res
            name = res.split('\n')[0].replace("1. 선정된 문화유산:", "").strip()
            st.session_state.history.append(name)

if st.session_state.report:
    st.divider()
    st.markdown(st.session_state.report)
    st.download_button("결과 파일 저장", st.session_state.report, file_name="korea_history_report.txt")
