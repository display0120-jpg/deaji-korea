import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 위치 조정
st.markdown("""
    <style>
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
    st.error("Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. 이미지 합성 함수 ---
def draw_on_image(uploaded_file, data):
    try:
        # 업로드된 파일을 이미지로 변환
        img = Image.open(uploaded_file).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 한글 폰트 설정 (Streamlit Cloud 환경)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        # 폰트가 없을 경우 기본 폰트 사용 (에러 방지)
        try:
            font_main = ImageFont.truetype(font_path, 22)
            font_small = ImageFont.truetype(font_path, 18)
            font_bold = ImageFont.truetype(font_path, 24)
        except:
            font_main = font_small = font_bold = ImageFont.load_default()

        # --- [좌표 설정] 사진 크기에 따라 미세 조정 필요 ---
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

        # 5~7. 인터뷰 내용 (좌표)
        draw.text((110, 600), f"Q: {data['q1']}", font=font_main, fill="black")
        draw.text((110, 630), f"A: {data['a1'][:60]}...", font=font_small, fill="black")

        draw.text((110, 850), f"Q: {data['q2']}", font=font_main, fill="black")
        draw.text((110, 880), f"A: {data['a2'][:60]}...", font=font_small, fill="black")

        draw.text((110, 1100), f"Q: {data['q3']}", font=font_main, fill="black")
        draw.text((110, 1130), f"A: {data['a3'][:60]}...", font=font_small, fill="black")

        # 8. 테마 탐방안
        draw.text((310, 1400), data['theme_title'], font=font_bold, fill="black")
        draw.text((310, 1480), data['theme_points'], font=font_small, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 실패: {e}")
        return None

# --- 4. AI 생성 함수 ---
def generate_ai_data(topic, history_list=[]):
    exclude = f"(이미 나온 {', '.join(history_list)} 절대 제외)" if history_list else ""
    prompt = f"""
    당신은 한국사 전문가입니다. 학생의 진로 '{topic}'와 실제로 직접적인 연관이 있는 한국 문화유산을 하나 선정하여 'JSON 형식'으로만 답변하세요.
    {exclude}
    억지로 연결하지 말고, 논리적 근거가 확실한 것만 고르세요.
    형식:
    {{
        "heritage": "이름", "reason": "선정 이유", "era": "시대", "location": "위치",
        "q1": "질문", "a1": "답변", "q2": "질문", "a2": "답변", "q3": "질문", "a3": "답변",
        "theme_title": "탐방 제목", "theme_points": "포인트 3가지"
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

# 세션 초기화
if 'history' not in st.session_state: st.session_state.history = []

# 사진 업로드 칸
uploaded_template = st.file_uploader("📋 빈 양식 사진(수행평가지)을 올려주세요", type=['jpg', 'jpeg', 'png'])

# 진로 입력 칸
user_input = st.text_input("나의 진로 또는 관심분야")

col1, col2 = st.columns(2)

if col1.button("수행평가 완성하기"):
    if user_input and uploaded_template:
        with st.spinner("AI가 분석하고 사진을 채우는 중..."):
            st.session_state.history = []
            data = generate_ai_data(user_input)
            if data:
                st.session_state.history = [data['heritage']]
                result_img = draw_on_image(uploaded_template, data)
                if result_img:
                    st.image(result_img, use_container_width=True)
                    # 다운로드 설정
                    buf = io.BytesIO()
                    result_img.save(buf, format="JPEG")
                    st.download_button("📸 완성 이미지 다운로드", buf.getvalue(), "completed_task.jpg", "image/jpeg")
    elif not uploaded_template:
        st.warning("먼저 양식 사진을 올려주세요.")
    else:
        st.warning("진로를 입력해주세요.")

if col2.button("다른 유산 추천 🔄"):
    if user_input and uploaded_template and st.session_state.history:
        with st.spinner("새로운 유산으로 교체 중..."):
            data = generate_ai_data(user_input, st.session_state.history)
            if data:
                st.session_state.history.append(data['heritage'])
                result_img = draw_on_image(uploaded_template, data)
                if result_img:
                    st.image(result_img, use_container_width=True)
                    buf = io.BytesIO()
                    result_img.save(buf, format="JPEG")
                    st.download_button("📸 새 이미지 다운로드", buf.getvalue(), "completed_task_new.jpg", "image/jpeg")
