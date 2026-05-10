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

# CSS: 우측 상단 문구 (더 낮게)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 200px; 
        right: 25px;
        color: #bbb;
        font-size: 0.7em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 진단 (가장 중요) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

# 키 공백 및 따옴표 완전 제거 (매우 중요)
api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

@st.cache_resource
def diagnostic_model_load():
    # 404 에러를 피하기 위한 시도
    candidates = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    errors = []
    
    for name in candidates:
        try:
            m = genai.GenerativeModel(name)
            # 작동 테스트 (가장 확실한 진단)
            m.generate_content("hi", generation_config={"max_output_tokens": 1})
            return m, None # 성공
        except Exception as e:
            errors.append(f"[{name}] {str(e)}")
            continue
    return None, errors

model, error_logs = diagnostic_model_load()

# --- 3. UI 부분 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

# 연결 실패 시 상세 에러 리포트 출력
if model is None:
    st.error("❌ 모든 AI 모델 연결 시도에 실패했습니다.")
    with st.expander("🛠️ 기술적 에러 로그 (이 내용을 복사해서 알려주세요)"):
        for log in error_logs:
            st.write(log)
    st.warning("💡 해결 방법: \n1. [Google AI Studio](https://aistudio.google.com/app/apikey)에서 새 키를 만드세요.\n2. Secrets에 따옴표 없이 키 값만 넣었는지 확인하세요.\n3. 앱을 Reboot 하세요.")
    st.stop()

# --- 4. 이미지 합성 함수 ---
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

        # 데이터 입력
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

# --- 5. AI 생성 로직 ---
def get_ai_data(topic, history=[]):
    exclude = f"(이미 추천된 {', '.join(history)} 제외)" if history else ""
    prompt = f"진로 '{topic}'와 관련된 한국 문화유산 선정해 JSON으로 답하세요. {exclude} 양식: heritage, reason, era, location, q1, a1, q2, a2, q3, a3, theme_title, theme_points."
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match: return json.loads(match.group())
        return None
    except Exception as e:
        st.error(f"데이터 생성 실패: {e}")
        return None

# --- 6. 실행 부분 ---
if 'history' not in st.session_state: st.session_state.history = []
if 'img' not in st.session_state: st.session_state.img = None

up_file = st.file_uploader("📋 양식 사진(JPG/PNG)을 올려주세요", type=['jpg','png','jpeg'])
user_in = st.text_input("나의 진로 또는 관심분야")

c1, c2 = st.columns(2)

def handle_click(is_new=True):
    if not up_file or not user_in:
        st.warning("사진과 진로를 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾는 중..."):
        if is_new: st.session_state.history = []
        data = get_ai_data(user_in, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
            res_img = draw_on_jpg(up_file, data)
            if res_img: st.session_state.img = res_img
        else: st.error("AI가 답변 형식을 지키지 못했습니다. 다시 시도해 주세요.")

if c1.button("수행평가(JPG) 완성하기"): handle_click(True)
if c2.button("다른 유산 추천 🔄"): handle_click(False)

if st.session_state.img:
    st.divider()
    st.image(st.session_state.img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.img.save(buf, format="JPEG")
    st.download_button("📸 이미지 다운로드", buf.getvalue(), "task.jpg", "image/jpeg")
