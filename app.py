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

# CSS: 우측 상단 문구
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 160px; 
        right: 25px;
        color: #ccc;
        font-size: 0.7em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 연결 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        target = next((p for p in preferences if p in available_models), available_models[0] if available_models else None)
        
        if target:
            # 안전 필터 최대한 해제 (역사적 사실 차단 방지)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            return genai.GenerativeModel(model_name=target, safety_settings=safety_settings)
        return None
    except Exception as e:
        st.error(f"모델 연결 오류: {e}")
        return None

model = get_working_model()

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

        # 데이터 입력 (좌표 보정)
        draw.text((250, 245), data.get('heritage', '내용 없음'), font=f_b, fill="black")
        r_lines = textwrap.wrap(data.get('reason', ''), width=45)
        for i, line in enumerate(r_lines[:2]):
            draw.text((250, 285 + (i*28)), line, font=f_s, fill="black")
        draw.text((250, 440), data.get('era', ''), font=f_m, fill="black")
        draw.text((250, 490), data.get('location', ''), font=f_m, fill="black")

        def write_qna(y, q, a):
            draw.text((115, y), f"Q: {q[:50]}", font=f_m, fill="black")
            a_lines = textwrap.wrap(a, width=65)
            for i, line in enumerate(a_lines[:2]):
                draw.text((115, y+30+(i*22)), f"A: {line}" if i==0 else f"   {line}", font=f_s, fill="black")

        write_qna(610, data.get('q1',''), data.get('a1',''))
        write_qna(860, data.get('q2',''), data.get('a2',''))
        write_qna(1110, data.get('q3',''), data.get('a3',''))
        draw.text((320, 1420), data.get('theme_title', ''), font=f_b, fill="black")
        draw.text((320, 1490), data.get('theme_points', ''), font=f_s, fill="black")
        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 내용 생성 및 파싱 ---
def get_ai_content(topic, history=[]):
    exclude = f"(이미 추천된 {', '.join(history)} 제외)" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생 진로 '{topic}'와 직접적 연관이 있는 한국 문화유산을 선정하세요. {exclude}
    반드시 아래 JSON 형식으로만 대답하세요. JSON 외의 설명이나 인사는 하지 마세요.

    {{
        "heritage": "이름", "reason": "선정 이유", "era": "시대", "location": "위치",
        "q1": "질문1", "a1": "답변1", "q2": "질문2", "a2": "답변2", "q3": "질문3", "a3": "답변3",
        "theme_title": "제목", "theme_points": "포인트"
    }}
    """
    try:
        res = model.generate_content(prompt)
        raw_text = res.text
        # 정규표현식으로 JSON 블록만 추출
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            st.error(f"AI 응답 형식이 올바르지 않습니다: {raw_text}")
            return None
    except Exception as e:
        st.error(f"API 요청 실패: {e}")
        return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'last_img' not in st.session_state: st.session_state.last_img = None

up_jpg = st.file_uploader("📋 빈 양식 사진을 올려주세요", type=['jpg','jpeg','png'])
user_job = st.text_input("나의 진로 또는 관심분야")

c1, c2 = st.columns(2)

def handle_click(is_reset=True):
    if not up_jpg or not user_job:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 분석 중..."):
        if is_reset: st.session_state.history = []
        data = get_ai_content(user_job, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
            res_img = draw_on_jpg(up_jpg, data)
            if res_img: st.session_state.last_img = res_img
        else:
            st.error("데이터를 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("수행평가(JPG) 완성하기"): handle_click(True)
if c2.button("다른 유산 추천 🔄"): handle_click(False)

if st.session_state.last_img is not None:
    st.divider()
    st.image(st.session_state.last_img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.last_img.save(buf, format="JPEG")
    st.download_button("📸 완성 이미지 저장", buf.getvalue(), "task.jpg", "image/jpeg")
