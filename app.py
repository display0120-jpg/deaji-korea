import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os
import re

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 AI 자동 완성기", layout="wide")

# CSS: 우측 상단 문구 (수행평가 방해 안 되게 아주 작고 아래로)
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

# --- 2. API 및 모델 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_ai_model():
    try:
        # 사용 가능한 모델 자동 탐색
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((p for p in ['models/gemini-1.5-flash', 'models/gemini-pro'] if p in available), available[0])
        s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        return genai.GenerativeModel(model_name=target, safety_settings=s_s)
    except: return None

model = get_ai_model()

# --- 3. 사진 위에 내용 그리기 함수 (정밀 좌표 반영) ---
def draw_content_on_image(image_file, data):
    try:
        # 1. 이미지 불러오기 및 표준화 (가로 1200px 기준)
        base_img = Image.open(image_file).convert("RGB")
        base_w = 1200
        w_percent = (base_w / float(base_img.size[0]))
        h_size = int((float(base_img.size[1]) * float(w_percent)))
        img = base_img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        
        # 2. 폰트 설정
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_title = ImageFont.truetype(font_path, 28) # 큰 제목용
            f_main = ImageFont.truetype(font_path, 22)  # 일반 내용용
            f_small = ImageFont.truetype(font_path, 19) # 세부 답변용
        except:
            f_title = f_main = f_small = ImageFont.load_default()

        # 3. 데이터 쓰기 (보내주신 양식 사진 위치 기준)
        def write(x, y, text, font, width=None):
            if not text: return
            if width:
                lines = textwrap.wrap(text, width=width)
                for i, line in enumerate(lines):
                    draw.text((x, y + (i * (font.size + 5))), line, font=font, fill="#222")
            else:
                draw.text((x, y), text, font=font, fill="#222")

        # [상단 정보 영역]
        write(255, 238, data.get('heritage', ''), f_title) # 유산명
        write(255, 275, data.get('reason', ''), f_small, width=45) # 선정 이유
        write(255, 345, data.get('era', ''), f_main) # 제작 시대
        write(255, 395, data.get('location', ''), f_main) # 현재 위치

        # [인터뷰 영역 - 박스 위치에 맞춰 배분]
        # 인터뷰 1
        write(115, 475, f"Q: {data.get('q1', '')}", f_main)
        write(115, 510, f"A: {data.get('a1', '')}", f_small, width=65)
        
        # 인터뷰 2
        write(115, 660, f"Q: {data.get('q2', '')}", f_main)
        write(115, 695, f"A: {data.get('a2', '')}", f_small, width=65)
        
        # 인터뷰 3
        write(115, 840, f"Q: {data.get('q3', '')}", f_main)
        write(115, 875, f"A: {data.get('a3', '')}", f_small, width=65)

        # [하단 탐방안 영역]
        write(310, 1075, data.get('theme_title', ''), f_title)
        write(310, 1145, data.get('theme_points', ''), f_small, width=55)

        return img
    except Exception as e:
        st.error(f"이미지 생성 중 에러가 발생했습니다: {e}")
        return None

# --- 4. AI 데이터 생성 로직 ---
def get_ai_response(topic, history=[]):
    if not model: return None
    h_str = f"(이전에 나온 {', '.join(history)}는 제외)" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생의 진로 '{topic}'와 실제로 깊은 연관이 있는 한국 문화유산을 하나 선정하세요. {h_str}
    반드시 아래 JSON 형식으로만 답하세요. 억지로 연결하지 말고 진짜 관련 있는 유산만 고르세요.
    {{ "heritage": "유산명", "reason": "선정이유(2줄)", "era": "시대", "location": "위치", "q1": "질문1", "a1": "답변1", "q2": "질문2", "a2": "답변2", "q3": "질문3", "a3": "답변3", "theme_title": "탐방제목", "theme_points": "포인트 3가지(문장으로)" }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except: return None

# --- 5. UI 및 실행 ---
st.title("🏛️ 한국사 수행평가 AI 자동 완성기")
st.write("양식 사진을 올리고 진로를 입력하면 AI가 직접 사진을 채워 드립니다.")

if 'history' not in st.session_state: st.session_state.history = []
if 'final_img' not in st.session_state: st.session_state.final_img = None

# 이미지 업로드 및 입력
up_file = st.file_uploader("📋 수행평가 양식 사진(JPG/PNG)을 업로드하세요", type=['jpg','png','jpeg'])
user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 의학, 디자인, 로봇공학 등")

c1, c2 = st.columns(2)

def handle_process(reset=True):
    if not up_file or not user_input:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("AI가 사진 양식을 분석하여 내용을 채우는 중..."):
        if reset: st.session_state.history = []
        data = get_ai_response(user_input, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage', ''))
            # 생성된 데이터를 이미지 위에 그리기
            result = draw_content_on_image(up_file, data)
            if result:
                st.session_state.final_img = result
        else:
            st.error("AI가 적절한 답변을 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("✨ 수행평가 사진 완성하기"):
    handle_process(reset=True)

if c2.button("🔄 다른 문화유산으로 바꾸기"):
    handle_process(reset=False)

# 결과물 출력
if st.session_state.final_img:
    st.divider()
    st.image(st.session_state.final_img, use_container_width=True, caption="AI가 완성한 수행평가지")
    
    # 다운로드용
    buf = io.BytesIO()
    st.session_state.final_img.save(buf, format="JPEG")
    st.download_button("📸 완성된 이미지 저장하기", buf.getvalue(), "completed_task.jpg", "image/jpeg")
