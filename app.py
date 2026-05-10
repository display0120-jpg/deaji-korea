import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import os

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

st.markdown("""
    <style>
    /* 우측 상단 상시 노출 문구 (작게) */
    .fixed-teacher-love {
        position: fixed;
        top: 100px; 
        right: 20px;
        color: #999;
        font-size: 0.85em;
        font-weight: normal;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.5);
        padding: 3px 8px;
        border-radius: 5px;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

@st.cache_resource
def get_model():
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

model = get_model()

# --- 3. 이미지 합성 함수 (좌표 포함) ---
def draw_on_template(data):
    if not os.path.exists("template.jpg"):
        st.error("template.jpg 파일을 찾을 수 없습니다. GitHub에 사진을 먼저 올려주세요.")
        return None
        
    try:
        img = Image.open("template.jpg").convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 한글 폰트 설정 (Streamlit Cloud 기본 경로)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        if not os.path.exists(font_path):
            # 로컬 테스트용 폰트 경로 (필요시 수정)
            font_path = "C:/Windows/Fonts/malgun.ttf" 
            
        try:
            font_main = ImageFont.truetype(font_path, 22)   # 일반 텍스트
            font_small = ImageFont.truetype(font_path, 18)  # 긴 답변용
            font_bold = ImageFont.truetype(font_path, 24)   # 유산 이름용
        except:
            font_main = font_small = font_bold = ImageFont.load_default()

        # --- [좌표 설정] 사진 칸에 맞게 글씨 입력 ---
        # 1. 선정한 문화유산
        draw.text((235, 240), data['heritage'], font=font_bold, fill="black")
        
        # 2. 선정 이유 (줄바꿈 처리)
        reason_lines = textwrap.wrap(data['reason'], width=45)
        for i, line in enumerate(reason_lines):
            draw.text((235, 275 + (i*28)), line, font=font_small, fill="black")
            
        # 3. 제작 시대
        draw.text((235, 435), data['era'], font=font_main, fill="black")
        
        # 4. 현재 위치
        draw.text((235, 485), data['location'], font=font_main, fill="black")

        # 5. 인터뷰 1 (생활/사상/정치)
        draw.text((110, 600), f"Q: {data['q1']}", font=font_main, fill="black")
        a1_lines = textwrap.wrap(data['a1'], width=65)
        for i, line in enumerate(a1_lines):
            draw.text((110, 630 + (i*25)), f"A: {line}" if i==0 else f"   {line}", font=font_small, fill="black")

        # 6. 인터뷰 2 (시련/변화)
        draw.text((110, 850), f"Q: {data['q2']}", font=font_main, fill="black")
        a2_lines = textwrap.wrap(data['a2'], width=65)
        for i, line in enumerate(a2_lines):
            draw.text((110, 880 + (i*25)), f"A: {line}" if i==0 else f"   {line}", font=font_small, fill="black")

        # 7. 인터뷰 3 (심화 관점)
        draw.text((110, 1100), f"Q: {data['q3']}", font=font_main, fill="black")
        a3_lines = textwrap.wrap(data['a3'], width=65)
        for i, line in enumerate(a3_lines):
            draw.text((110, 1130 + (i*25)), f"A: {line}" if i==0 else f"   {line}", font=font_small, fill="black")

        # 8. 테마 탐방안 (제목 및 포인트)
        draw.text((310, 1400), data['theme_title'], font=font_bold, fill="black")
        p_lines = textwrap.wrap(data['theme_points'], width=55)
        for i, line in enumerate(p_lines):
            draw.text((310, 1480 + (i*25)), line, font=font_small, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 오류: {e}")
        return None

# --- 4. AI 생성 함수 ---
def generate_ai_data(topic, history_list=[]):
    exclude = f"(이미 나온 {', '.join(history_list)}는 절대 제외)" if history_list else ""
    
    prompt = f"""
    당신은 한국사 전문가입니다. 학생의 진로 '{topic}'와 실제로 깊고 역사적인 연관이 있는 한국 문화유산을 하나 선정하여 'JSON 형식'으로만 답변하세요.
    {exclude}
    
    [중요] 억지로 끼워 맞추지 마세요. 논리적이고 실질적인 관련성이 있는 유산만 고르세요. 중복은 절대 금지입니다.

    JSON 형식:
    {{
        "heritage": "이름",
        "reason": "선정 이유(2줄 내외)",
        "era": "시대",
        "location": "위치",
        "q1": "질문", "a1": "답변",
        "q2": "질문", "a2": "답변",
        "q3": "질문(관점 명시)", "a3": "답변",
        "theme_title": "탐방 제목",
        "theme_points": "포인트 3가지(문장으로)"
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_str)
    except:
        return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")
st.write("진로를 입력하면 사진 양식에 맞춰 내용을 채워줍니다.")

if 'history' not in st.session_state: st.session_state.history = []

user_input = st.text_input("나의 진로 또는 관심분야")

col1, col2 = st.columns(2)

if col1.button("수행평가 양식 완성하기"):
    if user_input:
        with st.spinner("AI가 분석 중입니다..."):
            st.session_state.history = []
            data = generate_ai_data(user_input)
            if data:
                st.session_state.history = [data['heritage']]
                img = draw_on_template(data)
                if img:
                    st.image(img, use_container_width=True)
                    img.save("result.jpg")
                    with open("result.jpg", "rb") as f:
                        st.download_button("📸 완성 이미지 다운로드", f, "completed_task.jpg", "image/jpeg")
    else: st.warning("진로를 입력하세요.")

if col2.button("다른 유산 추천 🔄"):
    if user_input and st.session_state.history:
        with st.spinner("새로운 유산을 찾는 중..."):
            data = generate_ai_data(user_input, st.session_state.history)
            if data:
                st.session_state.history.append(data['heritage'])
                img = draw_on_template(data)
                if img:
                    st.image(img, use_container_width=True)
                    img.save("result.jpg")
                    with open("result.jpg", "rb") as f:
                        st.download_button("📸 다른 이미지 다운로드", f, "completed_task_new.jpg", "image/jpeg")
