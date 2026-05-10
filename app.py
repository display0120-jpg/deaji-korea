import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (더 작게, 더 아래로 배치)
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
        # 사용 가능한 모델 목록 가져오기
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        target = next((p for p in preferences if p in available_models), available_models[0] if available_models else None)
        
        if target:
            # 안전 필터 해제 (역사적 내용 차단 방지)
            s_s = [{"category": f"HARM_CATEGORY_{c}", "threshold": "BLOCK_NONE"} for c in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]]
            return genai.GenerativeModel(model_name=target, safety_settings=s_s)
        return None
    except: return None

model = get_working_model()

# --- 3. JPG 이미지 위에 글씨 쓰는 함수 ---
def draw_on_jpg(uploaded_file, data):
    try:
        # 업로드된 JPG 열기
        img = Image.open(uploaded_file).convert("RGB")
        
        # 좌표 기준을 맞추기 위해 이미지 크기 표준화 (너비 1200px)
        base_w = 1200
        w_percent = (base_w / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_w, h_size), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        
        # 한글 폰트 로드
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgun.ttf"
        
        try:
            f_m = ImageFont.truetype(font_path, 20) # 중간
            f_s = ImageFont.truetype(font_path, 17) # 작은
            f_b = ImageFont.truetype(font_path, 24) # 굵은
        except:
            f_m = f_s = f_b = ImageFont.load_default()

        # --- 사진 위 칸에 맞춰 내용 입력 (좌표) ---
        # 1. 문화유산 이름
        draw.text((250, 245), data.get('heritage', ''), font=f_b, fill="black")
        
        # 2. 선정 이유 (자동 줄바꿈)
        reason = data.get('reason', '')
        r_lines = textwrap.wrap(reason, width=42)
        for i, line in enumerate(r_lines[:2]):
            draw.text((250, 285 + (i*28)), line, font=f_s, fill="black")
            
        # 3. 제작 시대 / 4. 소재지
        draw.text((250, 440), data.get('era', ''), font=f_m, fill="black")
        draw.text((250, 490), data.get('location', ''), font=f_m, fill="black")

        # 5, 6, 7. 인터뷰 Q&A
        def write_qna(y, q, a):
            draw.text((115, y), f"Q: {q[:50]}", font=f_m, fill="black")
            a_lines = textwrap.wrap(a, width=65)
            for i, line in enumerate(a_lines[:2]):
                draw.text((115, y+30+(i*22)), f"A: {line}" if i==0 else f"   {line}", font=f_s, fill="black")

        write_qna(610, data.get('q1',''), data.get('a1',''))
        write_qna(860, data.get('q2',''), data.get('a2',''))
        write_qna(1110, data.get('q3',''), data.get('a3',''))

        # 8. 테마 탐방안
        draw.text((320, 1420), data.get('theme_title', ''), font=f_b, fill="black")
        draw.text((320, 1490), data.get('theme_points', ''), font=f_s, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 내용 생성 ---
def get_ai_content(topic, history=[]):
    exclude = f"(제외: {', '.join(history)})" if history else ""
    prompt = f"""
    당신은 한국사 전문가입니다. 학생 진로 '{topic}'와 실제로 깊은 연공이 있는 한국 문화유산을 선정해 내용을 만드세요. {exclude}
    억지로 연결하지 말고 실질적 근거가 확실한 것만 고르세요.
    반드시 아래 JSON 형식으로만 답하세요. (그 외 말은 하지 마세요)

    {{
        "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치",
        "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변",
        "theme_title": "제목", "theme_points": "포인트"
    }}
    """
    try:
        res = model.generate_content(prompt)
        t = res.text
        start, end = t.find('{'), t.rfind('}') + 1
        return json.loads(t[start:end])
    except: return None

# --- 5. UI 및 실행 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'final_jpg' not in st.session_state: st.session_state.final_jpg = None

# JPG 파일 업로드
up_jpg = st.file_uploader("📋 빈 양식 사진(JPG/PNG)을 올려주세요", type=['jpg','jpeg','png'])
user_job = st.text_input("나의 진로 또는 관심분야")

c1, c2 = st.columns(2)

def handle_click(is_reset=True):
    if not up_jpg or not user_job:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("가장 적절한 유산을 찾아 이미지(JPG)를 생성 중입니다..."):
        if is_reset: st.session_state.history = []
        data = get_ai_content(user_job, st.session_state.history)
        if data:
            st.session_state.history.append(data['heritage'])
            res_img = draw_on_jpg(up_jpg, data)
            if res_img: st.session_state.last_img = res_img
        else:
            st.error("AI가 내용을 찾지 못했습니다. 다시 시도해주세요.")

if c1.button("수행평가(JPG) 완성하기"): handle_click(True)
if c2.button("다른 유산 추천 🔄"): handle_click(False)

# 결과 이미지 출력 및 다운로드
if 'last_img' in st.session_state:
    st.divider()
    st.image(st.session_state.last_img, use_container_width=True)
    
    # 다운로드용 JPG 변환
    buf = io.BytesIO()
    st.session_state.last_img.save(buf, format="JPEG")
    st.download_button(
        label="📸 완성된 JPG 이미지 저장",
        data=buf.getvalue(),
        file_name="completed_history_task.jpg",
        mime="image/jpeg"
    )
