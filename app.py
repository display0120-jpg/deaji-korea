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

# CSS: 우측 상단 문구 (작고 눈에 덜 띄게 아래로 배치)
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

# --- 2. API 설정 및 모델 연결 (안전장치 강화) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_working_model():
    # 무료 한도가 가장 넉넉한 1.5-flash 모델을 우선적으로 찾습니다.
    candidates = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((p for p in candidates if p in available_models), None)
        
        if target:
            # 안전 필터 해제
            safety_settings = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
            return genai.GenerativeModel(model_name=target, safety_settings=safety_settings)
    except Exception as e:
        # 429 에러 등 발생 시 None 반환
        return None
    return None

# 전역 모델 변수 (안전하게 로드)
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

# --- 4. AI 내용 생성 ---
def get_ai_content(topic, history=[]):
    if model is None:
        st.error("🚨 AI 모델 연결이 불안정합니다. 잠시 후 다시 시도하거나 API 키를 확인해주세요.")
        return None

    exclude = f"(제외 유산 목록: {', '.join(history)})" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생의 진로 '{topic}'와 실질적으로 깊은 연관이 있는 한국 문화유산을 하나 선정하세요. {exclude}
    억지로 끼워 맞추지 말고 실제로 관련 있는 유산만 골라 아래 JSON 형식으로만 답하세요. 
    JSON: {{ "heritage": "...", "reason": "...", "era": "...", "location": "...", "q1": "...", "a1": "...", "q2": "...", "a2": "...", "q3": "...", "a3": "...", "theme_title": "...", "theme_points": "..." }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        if "429" in str(e):
            st.error("⏳ 사용량이 너무 많아 잠시 차단되었습니다. 30초 정도 기다렸다가 다시 눌러주세요.")
        else:
            st.error(f"데이터 생성 실패: {e}")
        return None

# --- 5. UI 및 버튼 로직 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'last_img' not in st.session_state: st.session_state.last_img = None

up_jpg = st.file_uploader("📋 빈 양식 사진을 올려주세요", type=['jpg','jpeg','png'])
user_job = st.text_input("나의 진로 또는 관심분야", placeholder="예: 의학, 디자인, 인공지능 등")

c1, c2 = st.columns(2)

def handle_click(is_reset=True):
    if model is None:
        st.error("AI 연결 상태를 확인할 수 없습니다. 페이지를 새로고침(Reboot) 해보세요.")
        return
    if not up_jpg or not user_job:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    
    with st.spinner("AI가 가장 적절한 유산을 분석 중입니다..."):
        if is_reset: st.session_state.history = []
        data = get_ai_content(user_job, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
            res_img = draw_on_jpg(up_jpg, data)
            if res_img:
                st.session_state.last_img = res_img
        else:
            st.info("AI가 답변을 생성하지 못했습니다. 버튼을 다시 한번 눌러보세요.")

if c1.button("수행평가(JPG) 완성하기"): handle_click(is_reset=True)
if c2.button("다른 유산 추천 🔄"): handle_click(is_reset=False)

if st.session_state.last_img is not None:
    st.divider()
    st.image(st.session_state.last_img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.last_img.save(buf, format="JPEG")
    st.download_button("📸 완성된 이미지 저장", buf.getvalue(), "completed_task.jpg", "image/jpeg")
