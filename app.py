import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="한국사 수행평가 도우미", layout="wide")

# 1. API 키 로드 및 클리닝
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Streamlit 설정(Secrets)에 GOOGLE_API_KEY가 없습니다!")
    st.stop()

# 키 앞뒤의 공백이나 따옴표를 완전히 제거합니다.
api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

# 2. 모델 로드 (에러가 나면 상세 내용을 화면에 표시)
@st.cache_resource
def init_model():
    # 시도할 모델 명칭
    names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    last_error = ""
    
    for name in names:
        try:
            m = genai.GenerativeModel(name)
            # 연결 확인을 위해 한 단어 테스트
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m, None
        except Exception as e:
            last_error = str(e)
            continue
    return None, last_error

model, error_msg = init_model()

# 연결 실패 시 안내
if model is None:
    st.error("🚨 AI 모델 연결에 실패했습니다!")
    st.warning(f"원인: {error_msg}")
    st.info("💡 해결방법: \n1. [Google AI Studio](https://aistudio.google.com/app/apikey)에서 새 키를 만드세요.\n2. Secrets에 GOOGLE_API_KEY = '새로운키' 라고 정확히 넣으세요.")
    st.stop()

# 3. 수행평가 생성 함수
def make_report(topic, history=[]):
    exclude = f"(이미 나온 {', '.join(history)} 제외)" if history else ""
    prompt = f"당신은 역사 교사입니다. 학생의 관심사 '{topic}'와 관련된 한국 문화유산 수행평가를 보고서 형식으로 작성하세요. {exclude} 양식: 선정유산, 선정 이유, 시대, 위치, 인터뷰 1/2/3, 탐방안."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"생성 실패: {str(e)}"

# 4. UI 화면
st.title("🏛️ 한국사 수행평가 AI")
st.success(f"✅ AI 연결됨: {model.model_name}")

if 'history' not in st.session_state: st.session_state.history = []
if 'text' not in st.session_state: st.session_state.text = ""

user_input = st.text_input("진로나 관심분야를 적어주세요")

c1, c2 = st.columns(2)
if c1.button("내용 생성"):
    if user_input:
        with st.spinner("작성 중..."):
            res = make_report(user_input)
            st.session_state.text = res
            st.session_state.history = [res.split('\n')[0]]
    else: st.warning("입력창을 채워주세요.")

if c2.button("다른 거 추천 🔄"):
    if user_input:
        with st.spinner("다시 찾는 중..."):
            res = make_report(user_input, st.session_state.history)
            st.session_state.text = res
            st.session_state.history.append(res.split('\n')[0])

if st.session_state.text:
    st.divider()
    st.markdown(st.session_state.text)
    st.download_button("결과 저장", st.session_state.text, file_name="report.txt")
