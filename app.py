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

# CSS: 우측 상단 문구 (더 작고 훨씬 낮게 배치)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        top: 250px; 
        right: 25px;
        color: #ddd;
        font-size: 0.6em;
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
def get_working_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        candidates = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        target = next((p for p in candidates if p in available), available[0] if available else None)
        if target:
            s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
            return genai.GenerativeModel(model_name=target, safety_settings=s_s)
    except: return None
    return None

model = get_working_model()

# --- 3. 이미지 합성 함수 (좌표 및 크기 전면 수정) ---
def draw_on_jpg(uploaded_file, data):
    try:
        img = Image.open(uploaded_file).convert("RGB")
        # 이미지 너비를 1200px로 고정하여 좌표 기준을 통일함
        base_w = 1200
        w_percent = (base_w / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        # 폰트 로드
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_title = ImageFont.truetype(font_path, 26) # 유산 이름용
            f_main = ImageFont.truetype(font_path, 21)  # 일반 텍스트용
            f_small = ImageFont.truetype(font_path, 19) # 긴 답변용
        except:
            f_title = f_main = f_small = ImageFont.load_default()

        # 데이터 안전하게 글자로 변환
        def g_v(key):
            v = data.get(key, '')
            return ", ".join(v) if isinstance(v, list) else str(v)

        # --- [새로운 좌표 설정] 양식 칸 위치에 정밀 조준 ---
        # 1. 선정한 문화유산 (Heritage)
        draw.text((260, 235), g_v('heritage'), font=f_title, fill="black")
        
        # 2. 선정 이유 (Reason) - 줄바꿈 처리
        r_txt = g_v('reason')
        r_lines = textwrap.wrap(r_txt, width=42)
        for i, line in enumerate(r_lines[:2]):
            draw.text((260, 275 + (i*28)), line, font=f_small, fill="black")
            
        # 3. 제작 시대 (Era)
        draw.text((260, 345), g_v('era'), font=f_main, fill="black")
        
        # 4. 현재 위치 (Location)
        draw.text((260, 395), g_v('location'), font=f_main, fill="black")

        # 인터뷰 영역 쓰기 함수
        def draw_interview(q_y, a_y, q_val, a_val):
            # 질문 입력
            draw.text((110, q_y), f"Q: {q_val[:55]}", font=f_main, fill="black")
            # 답변 입력 (줄바꿈)
            a_lines = textwrap.wrap(a_val, width=60)
            for i, line in enumerate(a_lines[:4]): # 최대 4줄까지
                draw.text((110, a_y + (i*25)), f"A: {line}" if i==0 else f"   {line}", font=f_small, fill="black")

        # 5. 인터뷰 1 (Y좌표 수정)
        draw_interview(475, 510, g_v('q1'), g_v('a1'))
        
        # 6. 인터뷰 2 (Y좌표 수정)
        draw_interview(655, 690, g_v('q2'), g_v('a2'))
        
        # 7. 인터뷰 3 (Y좌표 수정)
        draw_interview(835, 870, g_v('q3'), g_v('a3'))

        # 8. 테마 탐방안 (Y좌표 수정)
        draw.text((310, 1070), g_v('theme_title'), font=f_title, fill="black")
        tp_txt = g_v('theme_points')
        tp_lines = textwrap.wrap(tp_txt, width=50)
        for i, line in enumerate(tp_lines[:2]):
            draw.text((310, 1140 + (i*25)), line, font=f_small, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 중 오류 발생: {e}")
        return None

# --- 4. AI 데이터 생성 로직 ---
def get_ai_json(topic, history=[]):
    if not model: return None
    h_str = f"(제외: {', '.join(history)})" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생 진로 '{topic}'와 아주 밀접한 한국 문화유산을 하나 선정하세요. {h_str}
    반드시 아래 JSON 형식으로만 답하세요. 억지로 연결하지 마세요.
    JSON: {{ "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치", "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변", "theme_title": "제목", "theme_points": "포인트" }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match: return json.loads(match.group())
        return None
    except: return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'img' not in st.session_state: st.session_state.img = None

up_file = st.file_uploader("📋 빈 수행평가 양식 사진을 올려주세요", type=['jpg','png','jpeg'])
user_in = st.text_input("나의 진로나 관심분야 (예: 의학, 디자인, 건축 등)")

c1, c2 = st.columns(2)

def process(is_reset=True):
    if not up_file or not user_in:
        st.warning("사진을 올리고 진로를 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 분석하여 양식을 채우는 중..."):
        if is_reset: st.session_state.history = []
        data = get_ai_json(user_in, st.session_state.history)
        if data:
            st.session_state.history.append(str(data.get('heritage', '')))
            res_img = draw_on_jpg(up_file, data)
            if res_img: st.session_state.img = res_img
        else: st.error("AI가 답변을 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("수행평가(JPG) 완성하기"): process(True)
if c2.button("다른 유산 추천 🔄"): process(False)

if st.session_state.img:
    st.divider()
    st.image(st.session_state.img, use_container_width=True)
    buf = io.BytesIO()
    st.session_state.img.save(buf, format="JPEG")
    st.download_button("📸 완성 이미지 다운로드", buf.getvalue(), "result.jpg", "image/jpeg")
