import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os
import re

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 문화유산 탐구 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (더 작고 훨씬 낮게 배치)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 280px; 
        right: 30px;
        color: #eee;
        font-size: 0.55em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 자동 탐색 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_ai_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((p for p in ['models/gemini-1.5-flash', 'models/gemini-pro'] if p in available), available[0])
        # 안전 필터 해제
        s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        return genai.GenerativeModel(model_name=target, safety_settings=s_s)
    except: return None

model = get_ai_model()

# --- 3. 이미지 합성 함수 (오류 완벽 차단 로직) ---
def draw_content_on_image(image_file, data):
    try:
        base_img = Image.open(image_file).convert("RGB")
        base_w = 1200
        w_percent = (base_w / float(base_img.size[0]))
        h_size = int((float(base_img.size[1]) * float(w_percent)))
        img = base_img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_title = ImageFont.truetype(font_path, 28)
            f_main = ImageFont.truetype(font_path, 22)
            f_small = ImageFont.truetype(font_path, 18)
        except:
            f_title = f_main = f_small = ImageFont.load_default()

        # [안전장치] AI가 List 형태로 답변을 주었을 경우 String으로 강제 변환
        def get_safe_str(key):
            val = data.get(key, '')
            if isinstance(val, list):
                return " ".join(str(i) for i in val) # 목록일 경우 공백으로 합침
            return str(val)

        # 텍스트 그리기 함수
        def write(x, y, text, font, width=None):
            safe_text = get_safe_str(text) if isinstance(text, str) and text in data else str(text)
            if not safe_text: return
            if width:
                lines = textwrap.wrap(safe_text, width=width)
                for i, line in enumerate(lines[:5]): # 너무 길어지지 않게 제한
                    draw.text((x, y + (i * (font.size + 6))), line, font=font, fill="#222")
            else:
                draw.text((x, y), safe_text, font=font, fill="#222")

        # --- 이미지 좌표 조준 ---
        write(260, 238, 'heritage', f_title) # 문화유산 명
        write(260, 275, 'reason', f_small, width=45) # 선정 이유
        write(260, 345, 'era', f_main) # 시대
        write(260, 395, 'location', f_main) # 위치

        # 인터뷰 1, 2, 3
        write(115, 475, f"Q: {get_safe_str('q1')}", f_main)
        write(115, 505, get_safe_str('a1'), f_small, width=65)
        
        write(115, 655, f"Q: {get_safe_str('q2')}", f_main)
        write(115, 685, get_safe_str('a2'), f_small, width=65)
        
        write(115, 835, f"Q: {get_safe_str('q3')}", f_main)
        write(115, 865, get_safe_str('a3'), f_small, width=65)

        # 탐방안
        write(315, 1075, 'theme_title', f_title)
        write(315, 1145, 'theme_points', f_small, width=55)

        return img
    except Exception as e:
        st.error(f"이미지 생성 중 에러가 발생했습니다: {e}")
        return None

# --- 4. AI 데이터 생성 ---
def get_ai_response(topic, history=[]):
    if not model: return None
    h_str = f"(이전에 나온 {', '.join(history)}는 제외)" if history else ""
    prompt = f"""
    당신은 한국사 전문가입니다. 학생의 진로 '{topic}'와 연관된 한국 문화유산을 선정하세요. {h_str}
    반드시 아래 JSON 형식의 '단일 문장(String)'으로만 답하세요. 
    내용을 목록([ ])으로 만들지 말고 하나의 긴 문장으로 만드세요.

    {{ 
      "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치", 
      "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변", 
      "theme_title": "제목", "theme_points": "포인트 3가지를 한 문장으로" 
    }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except: return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")
st.write("양식 사진을 올리고 진로를 입력하면 AI가 직접 사진을 완성해 드립니다.")

if 'history' not in st.session_state: st.session_state.history = []
if 'final_img' not in st.session_state: st.session_state.final_img = None

up_file = st.file_uploader("📋 수행평가 양식 사진을 업로드하세요", type=['jpg','png','jpeg'])
user_input = st.text_input("나의 진로 또는 관심분야")

c1, c2 = st.columns(2)

def handle_process(reset=True):
    if not up_file or not user_input:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("AI가 분석하여 수행평가를 완성 중입니다..."):
        if reset: st.session_state.history = []
        data = get_ai_response(user_input, st.session_state.history)
        if data:
            st.session_state.history.append(str(data.get('heritage', '')))
            result = draw_content_on_image(up_file, data)
            if result:
                st.session_state.final_img = result
        else:
            st.error("AI가 데이터를 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("✨ 수행평가 사진 완성하기"):
    handle_process(reset=True)

if c2.button("🔄 다른 문화유산 추천하기"):
    handle_process(reset=False)

if st.session_state.final_img:
    st.divider()
    st.image(st.session_state.final_img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.final_img.save(buf, format="JPEG")
    st.download_button("📸 완성된 이미지 저장하기", buf.getvalue(), "completed_task.jpg", "image/jpeg")
