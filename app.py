import streamlit as st
import requests
import urllib.parse
import random

# --- 1. 관심 분야별 확장 데이터 (다시 추천 기능을 위해 여러 개 배치) ---
RECOMMEND_DATA = {
    "의학": [
        {"heritage": "동의보감", "reason": "유네스코 세계기록유산으로 등재된 의학 서적으로, 당시 동양 의학 지식을 집대성한 애민 정신의 상징입니다.", "link": "https://ko.wikipedia.org/wiki/동의보감"},
        {"heritage": "약사여래불", "reason": "질병을 고쳐준다는 부처로, 당시 사람들이 의학적 한계를 신앙으로 극복하려 했던 사상을 보여줍니다.", "link": "https://ko.wikipedia.org/wiki/약사여래"},
        {"heritage": "제중원", "reason": "한국 최초의 근대식 국립 서양식 병원으로, 전통 의학에서 근대 의학으로 넘어가는 전환점을 보여줍니다.", "link": "https://ko.wikipedia.org/wiki/제중원"}
    ],
    "작가": [
        {"heritage": "팔만대장경", "reason": "방대한 정보를 목판에 새긴 기록 문화의 정수로, 편집과 교정 기술의 극한을 보여주는 작가적 유산입니다.", "link": "https://ko.wikipedia.org/wiki/해인사_대장경판"},
        {"heritage": "직지심체요절", "reason": "세계 최고 금속 활자본으로, 정보 기록과 전파 방식의 혁신을 가져온 인쇄 문화의 핵심 유산입니다.", "link": "https://ko.wikipedia.org/wiki/직지심체요절"},
        {"heritage": "조선왕조실록", "reason": "철저한 객관성과 기록 정신을 바탕으로 한 사관들의 작가 정신이 깃든 방대한 역사 기록물입니다.", "link": "https://ko.wikipedia.org/wiki/조선왕조실록"}
    ],
    "IT/과학": [
        {"heritage": "측우기", "reason": "세계 최초의 우량계로, 자연 현상을 수치화하여 데이터로 관리하려 했던 과학적 사고의 산물입니다.", "link": "https://ko.wikipedia.org/wiki/측우기"},
        {"heritage": "첨성대", "reason": "신라의 천문 관측 시설로, 하늘의 데이터를 읽어 국가 운영에 활용했던 고대 과학 기술의 결정체입니다.", "link": "https://ko.wikipedia.org/wiki/첨성대"}
    ],
    "건축/디자인": [
        {"heritage": "수원 화성", "reason": "거중기를 이용한 과학적 축성법과 아름다운 성곽 디자인이 결합된 동양 성곽 건축의 백미입니다.", "link": "https://ko.wikipedia.org/wiki/수원_화성"},
        {"heritage": "불국사 석굴암", "reason": "완벽한 수학적 비례와 조각 예술이 만난 고대 건축 디자인의 정수입니다.", "link": "https://ko.wikipedia.org/wiki/석굴암"}
    ]
}

HEADERS = {'User-Agent': 'ModernHistoryApp/3.0'}

def get_wiki_summary(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

# --- 2. 페이지 설정 및 CSS (하트 애니메이션) ---
st.set_page_config(page_title="역사 수행 AI", layout="wide")

st.markdown("""
    <style>
    @keyframes heart_pop {
        0% { transform: scale(1); }
        50% { transform: scale(1.5); }
        100% { transform: scale(1); }
    }
    .heart-active {
        display: inline-block;
        font-size: 50px;
        animation: heart_pop 0.3s ease-out;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_state_msgs=True, unsafe_allow_html=True)

# --- 3. 사이드바: 팝업 하트 (20회 클릭 이벤트) ---
with st.sidebar:
    st.header("💖 하트 챌린지")
    if 'heart_count' not in st.session_state:
        st.session_state.heart_count = 0
    
    # 하트 버튼 누르면 카운트 증가 및 애니메이션 효과를 위해 리런
    if st.button("하트 꾹! ❤️"):
        st.session_state.heart_count += 1
    
    # 하트 시각화 (애니메이션 효과처럼 보이게 마크다운 사용)
    st.markdown(f'<div class="heart-active">❤️</div>', unsafe_allow_html=True)
    st.write(f"현재 클릭 수: **{st.session_state.heart_count}**번")

    # 20번 클릭 시 비밀 메시지
    if st.session_state.heart_count >= 20:
        st.error("🚨 비밀 폭로")
        st.subheader("변지원 바보")
        if st.button("기록 지우기"):
            st.session_state.heart_count = 0
            st.rerun()

# --- 4. 메인 화면 로직 ---
st.title("🏛️ 맞춤형 문화유산 탐구 & 다시 추천")

# 세션 상태 초기화
if 'current_recommendation' not in st.session_state:
    st.session_state.current_recommendation = None

user_interest = st.text_input("나의 관심 분야(의학, 작가 등)를 입력하세요", placeholder="예: 의학")

col_btn1, col_btn2 = st.columns([1, 4])

# [추천받기] 버튼
with col_btn1:
    if st.button("🔍 추천받기"):
        if user_interest:
            # 관심 키워드 포함 여부 확인
            match = None
            for key in RECOMMEND_DATA:
                if key in user_interest:
                    match = key
                    break
            
            if match:
                st.session_state.current_recommendation = random.choice(RECOMMEND_DATA[match])
            else:
                # 키워드 없으면 일반 검색 시도
                st.session_state.current_recommendation = {"heritage": user_interest, "reason": "입력하신 관심사와 관련된 역사적 연결고리를 탐구해보세요.", "link": f"https://ko.wikipedia.org/wiki/{user_interest}"}
        else:
            st.warning("분야를 입력해주세요.")

# [다시 추천] 버튼
with col_btn2:
    if st.button("🔄 별로야, 다시 추천해줘"):
        if user_interest:
            match = None
            for key in RECOMMEND_DATA:
                if key in user_interest:
                    match = key
                    break
            if match:
                # 현재와 다른 것을 뽑기 위해 셔플
                options = RECOMMEND_DATA[match]
                if len(options) > 1:
                    new_choice = random.choice([opt for opt in options if opt['heritage'] != st.session_state.current_recommendation.get('heritage')])
                    st.session_state.current_recommendation = new_choice
                else:
                    st.info("이 분야의 추천 데이터가 하나뿐입니다!")
            else:
                st.info("일반 검색 결과입니다. 다른 키워드를 입력해보세요.")

# --- 5. 결과 표시 ---
if st.session_state.current_recommendation:
    rec = st.session_state.current_recommendation
    data = get_wiki_summary(rec['heritage'])
    
    if data:
        st.divider()
        st.header(f"✨ 추천: {data['title']}")
        
        # 팩트 근거 섹션
        st.subheader("✅ 관련성 팩트 자료")
        st.success(f"**[{user_interest}]**와 관련 있는 명확한 이유:\n\n{rec['reason']}")
        st.link_button("🔗 팩트 확인 (공식 위키백과)", rec['link'])

        st.write("---")
        st.subheader("📑 수행평가 심화 인터뷰")

        c1, c2 = st.columns([1, 2])
        with c1:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'], width=300)
        with c2:
            st.info(f"Q: {data['title']}님, 당시 제작 과정에서 '{user_interest}'적 고민은 무엇이었나요?")
            st.write(f"A: 나는 당시 {user_interest}의 발전을 갈망하던 시대적 요구에 응답하기 위해 태어났어. 제작 과정의 치밀한 기록과 과학적 공법은 오늘날 전문가들이 보아도 놀랄 만큼 팩트에 기반한 정교함을 갖추고 있단다.")

        # 인터뷰 2 (시련)
        st.info("Q: 역사적 시련을 어떻게 극복하고 우리에게 남게 되었나요?")
        st.write(f"A: 전란과 약탈의 위기 속에서도 나를 지킨 건 이름 없는 민초들의 '기록에 대한 신념'이었어. 그들이 아니었다면 지금 너에게 {user_interest}의 역사적 증거를 보여줄 수 없었을 거야.")

        # 인터뷰 3 (관점)
        v = st.selectbox("탐구 관점 선택", ["비판적 관점", "융합적 관점", "비교사적 관점"])
        if "비판" in v:
            st.write("**Q: 제작 과정에서의 희생이나 권력 과시에 대해 어떻게 생각하나?**")
            st.write("**A:** 나의 화려함 뒤에는 백성들의 노역이 있었어. 하지만 그것이 소수를 위한 것인지, 세상을 이롭게 하려 한 것인지 팩트 기반으로 비판해보는 게 너의 과제란다.")
        elif "융합" in v:
            st.write(f"**Q: 현대 {user_interest} 기술과의 공통점은?**")
            st.write("**A:** 나의 설계 원리는 현대의 시스템 공학과 매우 닮아있어. 조상들의 융합적 사고가 얼마나 앞서갔는지 알 수 있는 대목이지.")
        else:
            st.write("**Q: 세계의 다른 유산과 비교했을 때의 독창성은?**")
            st.write("**A:** 비슷한 유산은 많지만, 나처럼 정교한 제작 방식과 보존 철학을 가진 유산은 드물어. 이게 우리 민족의 차별화된 실력이란다.")
