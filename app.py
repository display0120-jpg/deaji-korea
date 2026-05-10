import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os
import re

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (요청대로 더 작고 훨씬 낮게 배치)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 220px; 
        right: 25px;
        color: #ddd;
        font-size: 0.6em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 자동 탐색 (404 방지) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_working_model():
    try:
        # 내 API 키로 사용 가능한 모델 목록을 서버에서 조회
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        candidates = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        target = next((p for p in candidates if p in available), available[0] if available else None)
        
        if target:
            # 안전 필터 해제 (차단 방지)
            s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
            return genai.GenerativeModel(model_name=target, safety_settings=s_s)
    except: return None
    return None

model = get_working_model()

# --- 3. 이미지 합성 함수 (오류 방지 로직 강화) ---
def draw_on_jpg(uploaded_file, data):
    try:
        img = Image.open(uploaded_file).convert("RGB")
        base_w = 1200
        w_percent = (base_w / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_m, f_s, f_b = ImageFont.truetype(font_path, 20), ImageFont.truetype(font_path, 17), ImageFont.truetype(font_path, 24)
        except:
            f_m = f_s = f_b = ImageFont.load_default()

        # 데이터 안전하게 추출 (List일 경우 String으로 변환하여 오류 방지)
        def get_val(key):
            val = data.get(key, '')
            return ", ".join(val) if isinstance(val, list) else str(val)

        # [좌표 입력]
        draw.text((250, 245), get_val('heritage'), font=f_b, fill="black")
        
        reason_lines = textwrap.wrap(get_val('reason'), width=45)
        for i, line in enumerate(reason_lines[:2]):
            draw.text((250, 285 + (i*28)), line, font=f_s, fill="black")
            
        draw.text((250, 440), get_val('era'), font=f_m, fill="black")
        draw.text((250, 490), get_val('location'), font=f_m, fill="black")

        def write_qna(y, q, a):
            draw.text((115, y), f"Q: {q[:50]}", font=f_m, fill="black")
            a_lines = textwrap.wrap(a, width=65)
            for i, line in enumerate(a_lines[:2]):
                draw.text((115, y+30+(i*22)), f"A: {line}" if i==0 else f"   {line}", font=f_s, fill="black")

        write_qna(615, get_val('q1'), get_val('a1'))
        write_qna(865, get_val('q2'), get_val('a2'))
        write_qna(1115, get_val('q3'), get_val('a3'))

        draw.text((320, 1425), get_val('theme_title'), font=f_b, fill="black")
        draw.text((320, 1495), get_val('theme_points'), font=f_s, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 데이터 생성 ---
def get_ai_json(topic, history=[]):
    if not model: return None
    history_str = f"(제외: {', '.join(history)})" if history else ""
    
    prompt = f"""
    당신은 한국사 전문가입니다. 학생 진로 '{topic}'와 실제로 깊은 연관이 있는 한국 문화유산을 하나 선정하세요. {history_str}
    억지로 연결하지 말고 확실한 것만 골라 아래 JSON 형식으로만 답하세요.
    JSON: {{ "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치", "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변", "theme_title": "제목", "theme_points": "포인트" }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match: return json.loads(match.group())
        return None
    except: return None

# --- 5. UI 및 로직 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'img' not in st.session_state: st.session_state.img = None

up_file = st.file_uploader("📋 양식 사진(JPG/PNG)을 올려주세요", type=['jpg','png','jpeg'])
user_in = st.text_input("나의 진로 또는 관심분야 (예: 의학, 기계공학, 디자인 등)")

c1, c2 = st.columns(2)

def process(is_reset=True):
    if not up_file or not user_in:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾는 중..."):
        if is_reset: st.session_state.history = []
        data = get_ai_json(user_in, st.session_state.history)
        if data:
            # 히스토리에 유산 이름 추가 (중복 방지용)
            heritage_name = str(data.get('heritage', ''))
            st.session_state.history.append(heritage_name)
            
            res_img = draw_on_jpg(up_file, data)
            if res_img: st.session_state.img = res_img
        else:
            st.error("AI가 답변을 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("수행평가(JPG) 완성하기"): process(True)
if c2.button("다른 유산 추천 🔄"): process(False)

if st.session_state.img:
    st.divider()
    st.image(st.session_state.img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.img.save(buf, format="JPEG")
    st.download_button("📸 완성 이미지 다운로드", buf.getvalue(), "result.jpg", "image/jpeg")
