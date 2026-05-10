import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import textwrap
import io
import os
import re

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="한국사 문화유산 탐구 도우미AI", layout="wide")

# 우측 상단 문구 (아주 작게, 수행평가에 방해 안 되게 배치)
st.markdown("""
    <style>
    .fixed-teacher-love {
        position: fixed;
        bottom: 20px; 
        right: 30px;
        color: #ddd;
        font-size: 0.6em;
        z-index: 9999;
    }
    </style>
    <div class="fixed-teacher-love">국사쌤 사랑합니다 ❤️</div>
    """, unsafe_allow_html=True)

# --- 2. API 설정 ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"].strip().strip('"').strip("'"))

@st.cache_resource
def get_ai_model():
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((p for p in ['models/gemini-1.5-flash', 'models/gemini-pro'] if p in available), available[0])
        return genai.GenerativeModel(model_name=target)
    except: return None

model = get_ai_model()

# --- 3. 이미지 합성 함수 (정밀 좌표 및 폰트 크기 대폭 수정) ---
def draw_content_on_image(image_file, data):
    try:
        # 이미지 불러오기 및 표준 해상도(A4 비율 근처)로 고정
        base_img = Image.open(image_file).convert("RGB")
        target_w = 1500
        w_percent = (target_w / float(base_img.size[0]))
        target_h = int((float(base_img.size[1]) * float(w_percent)))
        img = base_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (크기를 키워서 가독성 확보)
        font_path = "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
        if not os.path.exists(font_path): font_path = "C:/Windows/Fonts/malgunbd.ttf" # 윈도우용
        
        try:
            f_title = ImageFont.truetype(font_path, 35) # 유산명용 (매우 크게)
            f_main = ImageFont.truetype(font_path, 26)  # 일반 칸용
            f_content = ImageFont.truetype(font_path, 22) # 인터뷰 답변용
        except:
            f_title = f_main = f_content = ImageFont.load_default()

        # 데이터 안전하게 가져오기
        def get_s(key):
            v = data.get(key, "")
            return " ".join(v) if isinstance(v, list) else str(v)

        # [좌표 재설정] - 1500px 너비 기준 양식 위치 조준
        # 1. 선정 문화유산
        draw.text((320, 240), get_s('heritage'), font=f_title, fill="#000")
        
        # 2. 선정 이유 (칸에 맞춰 줄바꿈)
        reason_txt = get_s('reason')
        reason_lines = textwrap.wrap(reason_txt, width=45)
        for i, line in enumerate(reason_lines[:2]):
            draw.text((320, 290 + (i*35)), line, font=f_content, fill="#333")
            
        # 3. 시대 / 4. 위치
        draw.text((320, 395), get_s('era'), font=f_main, fill="#000")
        draw.text((320, 445), get_s('location'), font=f_main, fill="#000")

        # 5. 인터뷰 1 (Q & A)
        draw.text((150, 540), f"Q. {get_s('q1')}", font=f_main, fill="#000")
        a1_lines = textwrap.wrap(get_s('a1'), width=60)
        for i, line in enumerate(a1_lines[:4]):
            draw.text((150, 580 + (i*30)), f"A. {line}" if i==0 else f"   {line}", font=f_content, fill="#333")

        # 6. 인터뷰 2
        draw.text((150, 755), f"Q. {get_s('q2')}", font=f_main, fill="#000")
        a2_lines = textwrap.wrap(get_s('a2'), width=60)
        for i, line in enumerate(a2_lines[:4]):
            draw.text((150, 795 + (i*30)), f"A. {line}" if i==0 else f"   {line}", font=f_content, fill="#333")

        # 7. 인터뷰 3
        draw.text((150, 970), f"Q. {get_s('q3')}", font=f_main, fill="#000")
        a3_lines = textwrap.wrap(get_s('a3'), width=60)
        for i, line in enumerate(a3_lines[:4]):
            draw.text((150, 1010 + (i*30)), f"A. {line}" if i==0 else f"   {line}", font=f_content, fill="#333")

        # 8. 테마 탐방안
        draw.text((350, 1220), get_s('theme_title'), font=f_title, fill="#000")
        tp_txt = get_s('theme_points')
        tp_lines = textwrap.wrap(tp_txt, width=50)
        for i, line in enumerate(tp_lines[:3]):
            draw.text((350, 1290 + (i*30)), f"• {line}", font=f_content, fill="#333")

        return img
    except Exception as e:
        st.error(f"이미지 생성 중 에러 발생: {e}")
        return None

# --- 4. AI 데이터 생성 ---
def get_ai_data(topic, history=[]):
    if not model: return None
    h_str = f"(제외 목록: {', '.join(history)})" if history else ""
    prompt = f"""
    당신은 고등학교 역사 전문가입니다. 학생의 진로 '{topic}'와 연관된 한국 문화유산을 하나 선정하세요. {h_str}
    반드시 아래 JSON 형식으로만 답하세요. 억지로 연결하지 말고 실질적인 역사 근거가 있는 것만 고르세요.
    답변은 목록([])이 아닌 하나의 긴 문자열(String)로 작성하세요.

    {{ 
      "heritage": "이름", "reason": "선정이유(구체적으로)", "era": "제작 시대", "location": "소재지", 
      "q1": "질문1", "a1": "답변1", "q2": "질문2", "a2": "답변2", "q3": "질문3", "a3": "답변3", 
      "theme_title": "탐방 제목", "theme_points": "포인트 3가지 요약" 
    }}
    """
    try:
        res = model.generate_content(prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        return json.loads(match.group()) if match else None
    except: return None

# --- 5. UI ---
st.title("🏛️ 한국사 문화유산 탐구 도우미AI")
st.info("양식 사진을 올리고 진로를 입력하면 빈칸을 채운 이미지를 만들어 드립니다.")

if 'history' not in st.session_state: st.session_state.history = []
if 'img_res' not in st.session_state: st.session_state.img_res = None

up_file = st.file_uploader("📋 수행평가 빈 양식 사진 업로드", type=['jpg','png','jpeg'])
user_input = st.text_input("나의 진로 또는 관심분야", placeholder="예: 의학, 로봇, 건축 등")

c1, c2 = st.columns(2)

def start_process(is_new=True):
    if not up_file or not user_input:
        st.warning("사진과 진로를 모두 입력해주세요.")
        return
    with st.spinner("AI가 분석하여 양식을 채우는 중입니다..."):
        if is_new: st.session_state.history = []
        data = get_ai_data(user_input, st.session_state.history)
        if data:
            st.session_state.history.append(data.get('heritage', ''))
            result = draw_content_on_image(up_file, data)
            if result:
                st.session_state.img_res = result
        else:
            st.error("AI가 데이터를 생성하지 못했습니다. 다시 시도해 주세요.")

if c1.button("✨ 수행평가 사진 완성하기"):
    start_process(is_new=True)

if c2.button("🔄 다른 문화유산 추천"):
    start_process(is_new=False)

if st.session_state.img_res:
    st.divider()
    st.image(st.session_state.img_res, use_container_width=True, caption="완성된 수행평가지")
    
    buf = io.BytesIO()
    st.session_state.img_res.save(buf, format="JPEG")
    st.download_button("📸 완성된 이미지 저장하기", buf.getvalue(), "completed_task.jpg", "image/jpeg")
