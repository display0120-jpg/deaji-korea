import streamlit as st
import google.generativeai as genai

# --- 1. 설정 및 보안 ---
# Secrets 확인
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Streamlit Cloud의 Settings > Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 2. 모델 로드 함수 (에러 방지용) ---
def get_model():
    # 1순위: gemini-1.5-flash (가장 빠름)
    # 2순위: gemini-1.5-pro
    # 3순위: gemini-pro (구버전이지만 안정적)
    model_names = ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # 모델이 실제로 작동하는지 가벼운 테스트
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    st.error("사용 가능한 Gemini 모델을 찾을 수 없습니다. API 키 권한을 확인해주세요.")
    st.stop()

model = get_model()

st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# --- 3. 프롬프트 함수 ---
def generate_heritage_report(user_interest, exclude_list=[]):
    exclude_text = f"이전에 추천한 것은 제외: {', '.join(exclude_list)}" if exclude_list else ""
    
    prompt = f"""
    당신은 고등학교 역사 선생님입니다. 
    학생의 관심사 '{user_interest}'와 관련된 한국 문화유산(구석기~조선) 하나를 선정해 수행평가를 작성하세요.
    {exclude_text}

    반드시 아래 형식을 지키세요:
    1. 선정된 문화유산: 이름
    2. 선정 이유: 관심사와 연결된 구체적 이유
    3. 제작 시대: 시대명
    4. 현재 위치: 주소
    5. 인터뷰 1 (생활/정치): Q&A 형식
    6. 인터뷰 2 (시련/현황): Q&A 형식
    7. 인터뷰 3 (비판/융합/비교 중 택1): 관점 명시 후 Q&A
    8. 탐방안: 제목과 포인트 3가지
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"내용 생성 중 에러가 발생했습니다: {str(e)}"

# --- 4. UI ---
st.title("🏛️ 한국사 수행평가 AI 도우미")

if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = ""

with st.sidebar:
    user_input = st.text_input("나의 진로/관심분야")
    col1, col2 = st.columns(2)
    with col1:
        submit = st.button("내용 생성")
    with col2:
        retry = st.button("다른 유산 🔄")

if submit and user_input:
    with st.spinner("작성 중..."):
        res = generate_heritage_report(user_input)
        st.session_state.current_report = res
        st.session_state.history = [res.split('\n')[0]]

if retry and user_input:
    with st.spinner("다시 찾는 중..."):
        res = generate_heritage_report(user_input, st.session_state.history)
        st.session_state.current_report = res
        st.session_state.history.append(res.split('\n')[0])

if st.session_state.current_report:
    st.markdown("---")
    st.markdown(st.session_state.current_report)
    st.download_button("결과 저장", st.session_state.current_report, file_name="history_task.txt")
