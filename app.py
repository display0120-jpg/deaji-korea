import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (작게, 위치 더 하향)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 150px; 
        right: 25px;
        color: #ddd;
        font-size: 0.7em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 자동 검색 (404 에러 완파) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

@st.cache_resource
def get_working_model():
    try:
        # 내 API 키가 접근 가능한 모델 목록을 서버에서 직접 가져옴
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 선호 순위: flash -> pro 순서
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        target_model = None
        for pref in preferences:
            if pref in available_models:
                target_model = pref
                break
        
        if not target_model and available_models:
            target_model = available_models[0]
            
        if target_model:
            m = genai.GenerativeModel(target_model)
            # 최종 연결 확인
            m.generate_content("hi", generation_config={"max_output_tokens": 1})
            return m, target_model
        return None, "사용 가능한 모델이 없습니다."
    except Exception as e:
        return None, str(e)

model, model_name = get_working_model()

if model is None:
    st.error("❌ AI 모델 연결에 실패했습니다.")
    st.info(f"🚩 에러 상세: {model_name}")
    st.warning("팁: API 키를 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 새로 발급받아보세요.")
    st.stop()

# --- 3. 이미지 합성 함수 (너비 표준화) ---
def draw_on_image(uploaded_file, data):
    try:
        img = Image.open(uploaded_file).convert("RGB")
        # 이미지 너비 1200px 기준 좌표 고정
        base_w = 1200
        w_percent = (base_w / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_m = ImageFont.truetype(font_path, 20)
            f_s = ImageFont.truetype(font_path, 17)
            f_b = ImageFont.truetype(font_path, 24)
        except:
            f_m = f_s = f_b = ImageFont.load_default()

        # [좌표 입력]
        draw.text((250, 245), data.get('heritage', ''), font=f_b, fill="black")
        
        r_lines = textwrap.wrap(data.get('reason', ''), width=45)
        for i, line in enumerate(r_lines[:2]):
            draw.text((250, 285 + (i*28)), line, font=f_s, fill="black")
            
        draw.text((250, 440), data.get('era', ''), font=f_m, fill="black")
        draw.text((250, 490), data.get('location', ''), font=f_m, fill="black")

        def draw_qna(y, q, a):
            draw.text((115, y), f"Q: {q[:50]}", font=f_m, fill="black")
            a_lines = textwrap.wrap(a, width=65)
            for i, line in enumerate(a_lines[:2]):
                draw.text((115, y+30+(i*22)), f"A: {line}" if i==0 else f"   {line}", font=f_s, fill="black")

        draw_qna(610, data.get('q1',''), data.get('a1',''))
        draw_qna(860, data.get('q2',''), data.get('a2',''))
        draw_qna(1110, data.get('q3',''), data.get('a3',''))

        draw.text((320, 1420), data.get('theme_title', ''), font=f_b, fill="black")
        draw.text((320, 1490), data.get('theme_points', ''), font=f_s, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 데이터 생성 (JSON 가이드 강화) ---
def get_ai_json(topic, history=[]):
    exclude = f"(이미 나온 {', '.join(history)} 제외)" if history else ""
    prompt = f"""
    당신은 한국사 전문가입니다. 학생 진로 '{topic}'와 '실제로 직접적인' 연관이 있는 한국 문화유산을 선정해 JSON으로만 답하세요. 
    {exclude}
    억지로 끼워 맞추지 말고 논리적 근거가 확실한 것만 고르세요.
    
    필수 형식:
    {{
        "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치",
        "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변",
        "theme_title": "제목", "theme_points": "포인트"
    }}
    """
    try:
        res = model.generate_content(prompt)
        t = res.text
        start, end = t.find('{'), t.rfind('}') + 1
        return json.loads(t[start:end])
    except: return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'img' not in st.session_state: st.session_state.img = None

up_file = st.file_uploader("📋 수행평가 양식 사진을 올려주세요", type=['jpg','png','jpeg'])
user_in = st.text_input("나의 진로 또는 관심분야")

c1, c2 = st.columns(2)

def process(is_new=True):
    if not up_file or not user_in:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾는 중..."):
        if is_new: st.session_state.history = []
        data = get_ai_json(user_in, st.session_state.history)
        if data:
            st.session_state.history.append(data['heritage'])
            res_img = draw_on_image(up_file, data)
            if res_img: st.session_state.img = res_img
        else: st.error("AI가 적절한 유산을 찾지 못했습니다. 다시 시도해주세요.")

if c1.button("수행평가 완성하기"): process(True)
if c2.button("다른 유산 추천 🔄"): process(False)

if st.session_state.img:
    st.divider()
    st.image(st.session_state.img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.img.save(buf, format="JPEG")
    st.download_button("📸 완성 이미지 다운로드", buf.getvalue(), "result.jpg", "image/jpeg")
