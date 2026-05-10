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
        top: 220px; 
        right: 25px;
        color: #ddd;
        font-size: 0.65em;
        font-weight: normal;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 및 모델 동적 탐색 (404 에러 완벽 해결) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'")
genai.configure(api_key=api_key)

@st.cache_resource
def get_working_model():
    try:
        # 내 API 키로 사용 가능한 모델 목록을 서버에서 직접 조회
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None, "사용 가능한 모델 목록을 가져오지 못했습니다."

        # 추천 모델 순위 (목록에 있는 것 중 가장 좋은 것 선택)
        candidates = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        target_name = None
        for cand in candidates:
            if cand in available_models:
                target_name = cand
                break
        
        if not target_name:
            target_name = available_models[0] # 아무거나 첫 번째 모델 선택

        # 안전 설정 (차단 방지)
        s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
        
        m = genai.GenerativeModel(model_name=target_name, safety_settings=s_s)
        # 작동 테스트
        m.generate_content("hi", generation_config={"max_output_tokens": 1})
        return m, target_name
    except Exception as e:
        return None, str(e)

model, active_model_name = get_working_model()

# --- 3. UI 및 에러 처리 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if model is None:
    st.error("❌ AI 모델 연결에 실패했습니다.")
    st.info(f"🚩 에러 상세: {active_model_name}")
    st.warning("팁: API 키 할당량이 끝났을 수 있습니다. 다른 구글 계정으로 새 키를 발급받아보세요.")
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

        # 데이터 입력 (좌표 보정)
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

# --- 5. AI 데이터 생성 ---
def get_ai_json(topic, history=[]):
    history_str = f"(제외: {', '.join(history)})" if history else ""
    prompt = f"""
    당신은 역사 전문가입니다. 학생 진로 '{topic}'와 직접적 연관이 있는 한국 문화유산을 하나 선정해 JSON으로만 답하세요. {history_str}
    JSON 형식: {{ "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치", "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변", "theme_title": "제목", "theme_points": "포인트" }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match: return json.loads(match.group())
        return None
    except Exception as e:
        if "429" in str(e): st.error("⏳ 할당량 초과! 1분 뒤에 시도하세요.")
        return None

# --- 6. 실행 부분 ---
if 'history' not in st.session_state: st.session_state.history = []
if 'img' not in st.session_state: st.session_state.img = None

up_file = st.file_uploader("📋 양식 사진(JPG/PNG)을 올려주세요", type=['jpg','png','jpeg'])
user_in = st.text_input("나의 진로 또는 관심분야 (예: 의학, 디자인, 로봇 등)")

c1, c2 = st.columns(2)

def process(is_reset=True):
    if not up_file or not user_in:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾는 중..."):
        if is_reset: st.session_state.history = []
        data = get_ai_json(user_in, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
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
    st.download_button("📸 이미지 다운로드", buf.getvalue(), "result.jpg", "image/jpeg")
