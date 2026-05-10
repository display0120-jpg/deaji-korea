import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="한국사 수행평가 도우미AI", layout="wide")

# CSS: 우측 상단 문구 (위치를 조금 내림)
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
        img = Image.open(uploaded_file).convert("RGB")
        
        # 이미지 크기에 상관없이 좌표를 맞추기 위해 너비 1200px로 표준화
        base_width = 1200
        w_percent = (base_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (Streamlit Cloud 환경의 일반적인 경로)
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
            "C:/Windows/Fonts/malgun.ttf" # 로컬 윈도우용
        ]
        
        font_main = None
        for path in font_paths:
            if os.path.exists(path):
                font_main = ImageFont.truetype(path, 22)
                font_small = ImageFont.truetype(path, 18)
                font_bold = ImageFont.truetype(path, 25)
                break
        
        if font_main is None:
            font_main = font_small = font_bold = ImageFont.load_default()

        # --- [좌표 설정] ---
        # 1. 문화유산 이름
        draw.text((250, 245), data.get('heritage', ''), font=font_bold, fill="black")
        
        # 2. 선정 이유
        reason_text = data.get('reason', '')
        lines = textwrap.wrap(reason_text, width=40)
        for i, line in enumerate(lines[:2]): # 최대 2줄
            draw.text((250, 285 + (i*30)), line, font=font_small, fill="black")
            
        # 3. 제작 시대 / 4. 위치
        draw.text((250, 445), data.get('era', ''), font=font_main, fill="black")
        draw.text((250, 495), data.get('location', ''), font=font_main, fill="black")

        # 5~7. 인터뷰 (요약형태로 입력)
        draw.text((120, 610), f"Q: {data.get('q1', '')}", font=font_main, fill="black")
        draw.text((120, 645), f"A: {data.get('a1', '')[:55]}...", font=font_small, fill="black")

        draw.text((120, 860), f"Q: {data.get('q2', '')}", font=font_main, fill="black")
        draw.text((120, 895), f"A: {data.get('a2', '')[:55]}...", font=font_small, fill="black")

        draw.text((120, 1110), f"Q: {data.get('q3', '')}", font=font_main, fill="black")
        draw.text((120, 1145), f"A: {data.get('a3', '')[:55]}...", font=font_small, fill="black")

        # 8. 탐방안
        draw.text((320, 1420), data.get('theme_title', ''), font=font_bold, fill="black")
        draw.text((320, 1490), data.get('theme_points', ''), font=font_small, fill="black")

        return img
    except Exception as e:
        st.error(f"이미지 생성 중 오류 발생: {e}")
        return None

# --- 4. AI 생성 함수 ---
def generate_ai_data(topic, history_list=[]):
    exclude = f"(이미 나온 {', '.join(history_list)} 제외)" if history_list else ""
    prompt = f"""
    당신은 한국사 전문가입니다. 학생의 진로 '{topic}'와 직접적인 연관이 있는 한국 문화유산을 하나 선정하여 반드시 아래 JSON 형식으로만 답변하세요.
    {exclude}
    억지로 연결하지 말고 실질적 근거가 있는 것만 고르세요.
    
    JSON 형식 예시:
    {{
        "heritage": "이름", "reason": "이유", "era": "시대", "location": "위치",
        "q1": "질문1", "a1": "답변1", "q2": "질문2", "a2": "답변2", "q3": "질문3", "a3": "답변3",
        "theme_title": "제목", "theme_points": "포인트"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # JSON 문자열만 추출하는 로직 강화
        text = response.text
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        json_str = text[start_idx:end_idx]
        return json.loads(json_str)
    except Exception as e:
        st.error(f"AI 답변 생성 실패: {e}")
        return None

# --- 5. UI 및 버튼 로직 ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")

if 'history' not in st.session_state: st.session_state.history = []
if 'last_img' not in st.session_state: st.session_state.last_img = None

# 파일 업로드와 진로 입력
uploaded_file = st.file_uploader("📋 수행평가 양식 사진을 올려주세요", type=['jpg', 'jpeg', 'png'])
user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 간호학, 자동차 공학, 인테리어 디자인 등")

col1, col2 = st.columns(2)

# 버튼 클릭 시 실행되는 함수
def run_process(is_new=True):
    if not uploaded_file:
        st.warning("먼저 사진을 업로드하세요.")
        return
    if not user_input:
        st.warning("진로를 입력하세요.")
        return

    with st.spinner("AI가 분석하고 이미지를 생성 중입니다..."):
        if is_new: st.session_state.history = []
        
        data = generate_ai_data(user_input, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage'))
            result_img = draw_on_image(uploaded_file, data)
            if result_img:
                st.session_state.last_img = result_img
                # 텍스트 데이터도 함께 표시 (확인용)
                st.success(f"선정된 유산: {data.get('heritage')}")
            else:
                st.error("이미지 합성에 실패했습니다.")
        else:
            st.error("AI가 올바른 데이터를 생성하지 못했습니다. 다시 시도해주세요.")

if col1.button("수행평가 완성하기"):
    run_process(is_new=True)

if col2.button("다른 유산 추천 🔄"):
    run_process(is_new=False)

# 결과 출력 (세션에 저장된 이미지가 있으면 항상 표시)
if st.session_state.last_img:
    st.divider()
    st.image(st.session_state.last_img, use_container_width=True)
    
    # 다운로드 버튼
    buf = io.BytesIO()
    st.session_state.last_img.save(buf, format="JPEG")
    st.download_button(
        label="📸 완성된 이미지 다운로드",
        data=buf.getvalue(),
        file_name="completed_history_task.jpg",
        mime="image/jpeg"
    )
