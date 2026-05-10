import streamlit as st
import requests

# --- 1. 진로/관심사별 문화유산 매핑 데이터 ---
CAREER_MAP = {
    "IT/개발/과학": ["첨성대", "측우기", "거북선", "수원 화성"],
    "의학/보건": ["동의보감", "약사여래불", "향약구급방"],
    "미술/디자인": ["고려청자", "백자 달항아리", "금동미미륵보살반가사유상"],
    "건축/토목": ["불국사", "석굴암", "해인사 장경판전", "남한산성"],
    "법/정치/사회": ["경국대전", "훈민정음", "직지심체요절"],
    "환경/지리": ["대동여지도", "고인돌", "강화 고인돌 유적"]
}

def get_wiki_summary(q):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{q.replace(' ', '_')}"
    res = requests.get(url, headers={'User-Agent': 'SchoolProject/1.0'})
    return res.json() if res.status_code == 200 else None

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="역사 수행평가 마스터", page_icon="🍎")

# --- 3. 사이드바: 점점 사라지는 사과 (재미 요소) ---
with st.sidebar:
    st.header("🍎 사과 먹기")
    if 'apple_stage' not in st.session_state:
        st.session_state.apple_stage = 0
    
    # 사과 상태 아이콘
    apples = ["🍎", "🍎(한입)", "🍎(반쪽)", "🍎(씨앗)", "✨(다시 생김!)"]
    st.title(apples[st.session_state.apple_stage])
    
    if st.button("사과 한입 먹기"):
        st.session_state.apple_stage = (st.session_state.apple_stage + 1) % len(apples)
    
    st.write("---")
    st.write("진로와 관심사를 입력하면")
    st.write("최적의 유산을 추천해드려요!")

# --- 4. 메인 화면 ---
st.title("📜 문화유산 탐구 수행평가 도우미")
st.info("안내문의 [가상 인터뷰]와 [탐방 기획안]을 한 번에 해결하세요.")

# 사용자 입력: 진로 및 관심사
col1, col2 = st.columns(2)
with col1:
    user_career = st.selectbox("나의 진로/관심사 분야", list(CAREER_MAP.keys()))
with col2:
    selected_heritage = st.selectbox("추천 문화유산 선택", CAREER_MAP[user_career])

if st.button("수행평가 내용 생성하기"):
    data = get_wiki_summary(selected_heritage)
    
    if data:
        summary = data.get('extract', '정보를 가져올 수 없습니다.')
        
        # --- 결과 출력: 수행평가 양식 ---
        st.divider()
        st.header(f"📍 [선정 문화유산: {selected_heritage}]")
        
        # 기본 정보
        st.subheader("1. 기본 정보")
        st.write(f"**- 선정 이유:** 저의 진로인 '{user_career}' 분야의 관점에서 {selected_heritage}에 담긴 조상들의 지혜와 기술력을 탐구하고 싶어 선정하게 되었습니다.")
        st.write(f"**- 제작 시대:** 위키백과 기준 시대 정보 참조")
        st.write(f"**- 현재 위치:** 대한민국 소재지")

        # 인터뷰 1
        st.subheader("2. 인터뷰 1 (생활/사상/정치)")
        st.warning(f"Q: {selected_heritage}님, 당신이 만들어질 당시 사람들은 어떤 생각을 가지고 당신을 만들었나요?")
        st.write(f"A: 나는 당시 사람들의 {user_career}에 대한 열망과 믿음을 담아 만들어졌단다. 기록에 따르면 '{summary[:100]}...' 와 같은 배경 속에서 탄생하여 많은 이들에게 희망이 되었지.")

        # 인터뷰 2
        st.subheader("3. 인터뷰 2 (역사적 시련/변화)")
        st.warning(f"Q: 세월을 거치며 겪은 가장 기억에 남는 시련은 무엇인가요?")
        st.write(f"A: 오랜 세월 전쟁과 기후 변화를 견디며 일부가 소실되기도 했지만, 지금은 그 가치를 인정받아 국가적인 보호를 받고 있어. 덕분에 지금의 너와 만날 수 있게 된 거란다.")

        # 인터뷰 3 (통합적 관점)
        st.subheader("4. 인터뷰 3 (비판적/융합적 관점)")
        st.warning(f"Q: (융합적 관점) 당신 속에 담긴 특별한 과학적 혹은 예술적 원리는 무엇인가요?")
        st.write(f"A: 나를 자세히 보렴. 나의 구조 안에는 현대의 '{user_career}'적 시각으로 보아도 놀라운 정교함이 숨겨져 있어. 이는 단순히 예쁜 것이 아니라 치밀한 계산과 장인 정신이 합쳐진 결과물이지.")

        # 탐방 기획안
        st.subheader("5. 테마 탐방 기획안")
        st.success(f"**기획 제목:** [ {user_career}의 눈으로 본 ] {selected_heritage}의 숨겨진 비밀 투어")
        st.write(f"**필수 관람 포인트:** {selected_heritage}의 가장 세밀한 부분을 먼저 관찰하세요. 그 속에 숨겨진 조상들의 '{user_career}'적 설계를 직접 확인하며 감상하는 것이 핵심입니다.")
        
    else:
        st.error("데이터를 가져오는 중 오류가 발생했습니다.")

st.divider()
st.caption("본 AI 도우미는 위키백과 정보를 바탕으로 수행평가의 뼈대를 잡아줍니다. 자신의 생각을 더해 완성도를 높이세요!")
