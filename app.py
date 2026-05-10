import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (더 작게, 더 아래로)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 140px; 
        right: 25px;
        color: #ccc;
        font-size: 0.7em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 및 모델 연결 (에러 상세 분석) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

# 키 공백 및 따옴표 완전 제거
api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

@st.cache_resource
def load_available_model():
    # 최신 모델 명칭 후보군
    candidates = [
        'gemini-1.5-flash-latest', 
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash',
        'gemini-pro'
    ]
    last_error = ""
    
    for name in candidates:
        try:
            m = genai.GenerativeModel(name)
            # 연결 테스트 (실제 호출)
            m.generate_content("hi", generation_config={"max_output_tokens": 1})
            return m, None
        except Exception as e:
            last_error = str(e)
            continue
    return None, last_error

model, error_log = load_available_model()

# 연결 실패 시 구체적인 이유 출력
if model is None:
    st.error("❌ AI 모델 연결에 실패했습니다.")
    st.info(f"🚩 구글 서버의 에러 메시지: {error_log}")
    st.warning("💡 해결방법: \n1. [Google AI Studio](https://aistudio.google.com/app/apikey)에서 'Create API key in new project'로 새 키를 만드세요.\n2. 새 키를 Secrets에 다시 등록하고 앱을 Reboot 하세요.")
    st.stop()

# --- 3. 이미지 합성 함수 ---
def draw_on_image(uploaded_file, data):
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
            f_m = ImageFont.truetype(font_path, 20)
            f_s = ImageFont.truetype(font_path, 17)
            f_b = ImageFont.truetype(font_path, 24)
        except:
            f_m = f_s = f_b = ImageFont.load_default()

        # [좌표 입력]
        draw.text((250, 245), data.get('heritage', ''), font=f_b, fill="black")
        
        r_lines = textwrap.wrap(data.get('reason', ''), width=42)
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

# --- 4. AI 데이터 생성 ---
def get_ai_json(topic, history=[]):
    exclude = f"(이미 나온 {', '.join(history)} 제외)" if history else ""
    prompt = f"학생 진로 '{topic}'와 연관된 한국 문화유산을 선정해 JSON으로 답하세요. {exclude} 선정유산, 선정 이유, 시대, 위치, 인터뷰 1/2/3, 탐방안 포함."
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
    with st.spinner("AI가 분석 중..."):
        if is_new: st.session_state.history = []
        data = get_ai_json(user_in, st.session_state.history)
        if data:
            st.session_state.history.append(data['heritage'])
            res_img = draw_on_image(up_file, data)
            if res_img: st.session_state.img = res_img
        else: st.error("AI가 데이터를 만들지 못했습니다. 다시 시도해주세요.")

if c1.button("수행평가 완성하기"): process(True)
if c2.button("다른 유산 추천 🔄"): process(False)

if st.session_state.img:
    st.divider()
    st.image(st.session_state.img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.img.save(buf, format="JPEG")
    st.download_button("📸 완성 이미지 다운로드", buf.getvalue(), "task.jpg", "image/jpeg")
