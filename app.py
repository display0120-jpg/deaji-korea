import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 1. API 키 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

# 2. 사용 가능한 모델 자동 검색 (404 에러 해결 핵심)
@st.cache_resource
def get_best_available_model():
    try:
        # 내 API 키로 사용 가능한 모델 목록을 가져옴
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 선호하는 모델 순서
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        for pref in preferences:
            if pref in available_models:
                m = genai.GenerativeModel(pref)
                # 실제 작동 테스트
                m.generate_content("test", generation_config={"max_output_tokens": 1})
                return m, pref
        
        # 만약 목록에 없으면 첫 번째 사용 가능한 모델 선택
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
    st.info("💡 해결법: \n1. Google AI Studio에서 '새로운 API 키'를 만드세요.\n2. API 키가 활성화될 때까지 1~2분 기다린 후 Reboot 하세요.")
    st.stop()

# 3. 수행평가 생성 함수
def generate_history_report(topic, history_list=[]):
    exclude = f"(이미 나온 {', '.join(history_list)} 제외)" if history_list else ""
    
    prompt = f"""
    당신은 역사 전문가입니다. 학생의 진로/관심사 '{topic}'와 관련된 한국 문화유산(구석기~조선) 수행평가 보고서를 작성하세요. {exclude}
    
    양식:
    1. 선정된 문화유산: 이름
    2. 선정 이유: 진로와 연결된 이유
    3. 제작 시대: 시대
    4. 현재 위치: 소재지
    5. 인터뷰 1(생활/정치): Q&A
    6. 인터뷰 2(시련/변화): Q&A
    7. 인터뷰 3(비판/융합/비교 중 택1): 관점 명시 후 Q&A
    8. 탐방안: 제목과 포인트 3가지
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"생성 실패: {str(e)}"

# 4. UI 구성
st.title("🏛️ 한국사 수행평가 AI")
st.success(f"✅ AI 모델 연결 성공! (사용 중인 모델: {model_name})")

if 'history' not in st.session_state: st.session_state.history = []
if 'report' not in st.session_state: st.session_state.report = ""

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

if st.session_state.report:
    st.divider()
    st.markdown(st.session_state.report)
    st.download_button("결과 저장", st.session_state.report, file_name="report.txt")
