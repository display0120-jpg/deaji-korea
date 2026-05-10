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

# CSS: 우측 상단 문구 (작고 낮게 배치)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 180px; 
        right: 25px;
        color: #bbb;
        font-size: 0.7em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 자동 연결 (404 에러 해결사) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

@st.cache_resource
def get_best_model():
    # 404 에러를 피하기 위해 다양한 모델 명칭 후보를 시도합니다.
    candidates = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    for name in candidates:
        try:
            m = genai.GenerativeModel(model_name=name, safety_settings=safety)
            # 작동 테스트 (가장 중요한 부분)
            m.generate_content("hi", generation_config={"max_output_tokens": 1})
            return m
        except Exception:
            continue
    return None

model = get_best_model()

# --- 3. 이미지 합성 함수 ---
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

        # [좌표 입력 - 이미지 비율에 맞춰 입력]
        draw.text((250, 245), data.get('heritage', ''), font=f_b, fill="black")
        r_lines = textwrap.wrap(data.get('reason', ''), width=45)
        for i, line in enumerate(r_lines[:2]):
            draw.text((250, 285 + (i*30)), line, font=f_s, fill="black")
        draw.text((250, 445), data.get('era', ''), font=f_m, fill="black")
        draw.text((250, 495), data.get('location', ''), font=f_m, fill="black")

        def write_qna(y, q, a):
            draw.text((115, y), f"Q: {q[:50]}", font=f_m, fill="black")
            a_lines = textwrap.wrap(a, width=65)
            for i, line in enumerate(a_lines[:2]):
                draw.text((115, y+35+(i*22)), f"A: {line}" if i==0 else f"   {line}", font=f_s, fill="black")

        write_qna(615, data.get('q1',''), data.get('a1',''))
        write_qna(865, data.get('q2',''), data.get('a2',''))
        write_qna(1115, data.get('q3',''), data.get('a3',''))
        draw.text((320, 1425), data.get('theme_title', ''), font=f_b, fill="black")
        draw.text((320, 1495), data.get('theme_points', ''), font=f_s, fill="black")
        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 내용 생성 및 JSON 파싱 ---
def get_ai_content(topic, history=[]):
    if model is None:
        st.error("❌ AI 모델 연결에 실패했습니다. API 키를 확인해주세요.")
        return None

    exclude = f"(이전에 나온 {', '.join(history)}는 제외)" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생 진로 '{topic}'와 직접적 연관이 있는 한국 문화유산을 선정해 JSON으로만 답하세요. {exclude}
    형식: {{ "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치", "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변", "theme_title": "제목", "theme_points": "포인트" }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        st.error(f"⚠️ 생성 중 오류 발생: {e}")
        return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'last_img' not in st.session_state: st.session_state.last_img = None

up_file = st.file_uploader("📋 양식 사진(JPG/PNG)을 올려주세요", type=['jpg','jpeg','png'])
user_job = st.text_input("나의 진로 또는 관심분야 (예: 의학, IT, 건축)")

c1, c2 = st.columns(2)

def handle_click(reset_h=True):
    if not up_file or not user_job:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾는 중..."):
        if reset_h: st.session_state.history = []
        data = get_ai_content(user_job, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
            res_img = draw_on_jpg(up_file, data)
            if res_img: st.session_state.last_img = res_img
        else:
            st.info("다시 한 번 눌러주세요.")

if c1.button("수행평가 완성하기"): handle_click(True)
if c2.button("다른 유산 추천 🔄"): handle_click(False)

if st.session_state.last_img:
    st.divider()
    st.image(st.session_state.last_img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.last_img.save(buf, format="JPEG")
    st.download_button("📸 이미지 다운로드", buf.getvalue(), "task.jpg", "image/jpeg")
