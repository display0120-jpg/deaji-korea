import streamlit as st
import requests
import urllib.parse
import random

# --- 1. 데이터베이스 강화 (더 많은 분야와 유산 추가) ---
RECOMMEND_DATA = {
    "의학": [
        {"heritage": "동의보감", "reason": "유네스코 세계기록유산으로, 당시 동양 의학 지식을 집대성한 애민 정신의 결정체입니다.", "link": "https://ko.wikipedia.org/wiki/동의보감"},
        {"heritage": "제중원", "reason": "한국 최초의 근대식 국립 서양식 병원으로, 의학의 근대화 과정을 보여주는 핵심 유산입니다.", "link": "https://ko.wikipedia.org/wiki/제중원"},
        {"heritage": "향약구급방", "reason": "고려 시대 우리 땅의 약재를 정리한 현존 최고(最古)의 의학서입니다.", "link": "https://ko.wikipedia.org/wiki/향약구급방"}
    ],
    "작가": [
        {"heritage": "팔만대장경", "reason": "오자 없는 완벽한 편집과 기록을 보여주는 목판 인쇄술의 정수로, 작가적 정밀함의 상징입니다.", "link": "https://ko.wikipedia.org/wiki/해인사_대장경판"},
        {"heritage": "직지심체요절", "reason": "세계에서 가장 오래된 금속 활자본으로, 정보의 기록과 전파를 혁신한 인류적 유산입니다.", "link": "https://ko.wikipedia.org/wiki/직지심체요절"},
        {"heritage": "조선왕조실록", "reason": "사관들의 철저한 기록 정신과 객관성을 보여주는 방대한 역사 기록물입니다.", "link": "https://ko.wikipedia.org/wiki/조선왕조실록"}
    ],
    "미술/디자인": [
        {"heritage": "고려청자", "reason": "비색과 상감 기법이라는 독창적인 예술성을 통해 당시 세계 최고의 공예 디자인을 보여줍니다.", "link": "https://ko.wikipedia.org/wiki/고려청자"},
        {"heritage": "백자 달항아리", "reason": "절제미와 곡선미의 정수로, 현대 미술가들에게도 영감을 주는 한국적 디자인의 극치입니다.", "link": "https://ko.wikipedia.org/wiki/백자_달항아리"}
    ],
    "과학/IT": [
        {"heritage": "첨성대", "reason": "천문 데이터를 수집하고 분석했던 고대 과학의 상징으로, 데이터 분석의 초기 형태를 보여줍니다.", "link": "https://ko.wikipedia.org/wiki/첨성대"},
        {"heritage": "거중기", "reason": "도르래 원리를 이용해 무거운 돌을 옮긴 건축 공학의 혁신적 사례입니다.", "link": "https://ko.wikipedia.org/wiki/거중기"}
    ]
}

HEADERS = {'User-Agent': 'HeritageSupport/4.0'}

def get_wiki_summary(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
    except:
        return None
    return None

# --- 2. 화면 구성 및 CSS (하트 애니메이션) ---
st.set_page_config(page_title="역사 수행평가 팩트체크", layout="wide")

# 하트 커지는 애니메이션 효과
st.markdown("""
    <style>
    @keyframes heart_pop {
        0% { transform: scale(1); }
        50% { transform: scale(1.6); color: #ff4b4b; }
        100% { transform: scale(1); }
    }
    .heart-style {
        font-size: 80px;
        text-align: center;
        cursor: pointer;
        user-select: none;
    }
    .heart-anim {
        animation: heart_pop 0.4s ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바: 하트와 비밀 메시지 ---
with st.sidebar:
    st.header("💖 하트 팝업")
    if 'heart_cnt' not in st.session_state:
        st.session_state.heart_cnt = 0
    if 'pop_trigger' not in st.session_state:
        st.session_state.pop_trigger = False

    if st.button("하트 누르기 ❤️"):
        st.session_state.heart_cnt += 1
        st.session_state.pop_trigger = True
    else:
        st.session_state.pop_trigger = False

    # 클릭 시 애니메이션 클래스 적용
    anim_class = "heart-anim" if st.session_state.pop_trigger else ""
    st.markdown(f'<div class="heart-style {anim_class}">❤️</div>', unsafe_allow_html=True)
    st.write(f"클릭 수: **{st.session_state.heart_cnt}**번")

    if st.session_state.heart_cnt >= 20:
        st.error("🚨 비밀 메시지")
        st.subheader("변지원 바보")
        if st.button("카운트 리셋"):
            st.session_state.heart_cnt = 0
            st.rerun()

# --- 4. 메인 화면 ---
st.title("📜 관심사 맞춤 문화유산 & 팩트체크")
st.write("관심 분야를 입력하면 **명확한 근거**가 있는 유산을 추천하고 인터뷰를 작성합니다.")

if 'selected_rec' not in st.session_state:
    st.session_state.selected_rec = None

user_in = st.text_input("나의 관심 분야 (예: 의학, 작가, 미술, IT)", placeholder="키워드를 입력하세요")

c1, c2 = st.columns([1, 4])

with c1:
    if st.button("🔍 추천받기"):
        if user_in:
            match = next((k for k in RECOMMEND_DATA if k in user_in), None)
            if match:
                st.session_state.selected_rec = random.choice(RECOMMEND_DATA[match])
            else:
                st.session_state.selected_rec = {"heritage": user_in, "reason": "이 유산은 해당 분야의 선구적인 역할을 했습니다.", "link": f"https://ko.wikipedia.org/wiki/{user_in}"}
        else:
            st.warning("분야를 먼저 입력하세요.")

with c2:
    if st.button("🔄 다른 유산 추천"):
        if user_in:
            match = next((k for k in RECOMMEND_DATA if k in user_in), None)
            if match:
                current_h = st.session_state.selected_rec.get('heritage') if st.session_state.selected_rec else ""
                options = [o for o in RECOMMEND_DATA[match] if o['heritage'] != current_h]
                if options:
                    st.session_state.selected_rec = random.choice(options)
                else:
                    st.info("이 분야의 추천 데이터가 하나입니다!")
            else:
                st.info("다른 키워드를 입력해보세요.")

# --- 5. 수행평가 결과 ---
if st.session_state.selected_rec:
    rec = st.session_state.selected_rec
    data = get_wiki_summary(rec['heritage'])
    
    if data:
        st.divider()
        st.header(f"🏛️ 탐구 대상: {data['title']}")
        
        # 팩트 섹션
        st.subheader("✅ 선정 근거 및 팩트")
        st.success(f"**[{user_in}]** 분야와 관련된 이유: {rec['reason']}")
        st.link_button("🔗 팩트 확인 (위키백과 상세 자료)", rec['link'])
        
        st.write("---")
        st.subheader("💬 수행평가 심화 인터뷰")
        
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'])
        with col_txt:
            st.info(f"Q: {data['title']}님, 당신의 가치를 '{user_in}'적 관점에서 설명해 주세요.")
            st.write(f"A: 나는 당시 {user_in} 분야의 발전을 갈망하던 시대의 요구로 탄생했어. 기록에 남아있듯 나의 정교한 제작 방식과 목적은 단순한 장식을 넘어 실질적인 변화를 이끌었단다.")

        st.info("Q: 세월을 거치며 겪은 역사적 시련은 무엇이었나요?")
        st.write("A: 전쟁으로 인해 유실될 뻔한 위기도 있었지만, 기록을 소중히 여긴 우리 민족의 신념 덕분에 지금 너희 곁에 남아있을 수 있었지. 이것이 바로 살아있는 역사란다.")

        # 관점 선택 인터뷰
        view = st.radio("인터뷰 3 관점", ["비판적 관점", "융합적 관점", "비교사적 관점"])
        st.write(f"**[{view}] 상세 답변**")
        if "비판" in view:
            st.write("Q: 제작 과정에서 백성들의 희생이 크지 않았나요?\n\n**A:** 나의 탄생 뒤에는 수많은 백성의 노역이 있었어. 그 희생이 정당했는지, 아니면 누군가의 권력을 위한 것이었는지 비판적으로 고민해보는 게 너의 과제야.")
        elif "융합" in view:
            st.write(f"Q: 현대 기술과의 공통점은?\n\n**A:** 나의 설계에는 현대 시스템 공학과 유사한 데이터 분류와 정밀 공정이 숨어있어. 조상들의 융합적 지혜를 엿볼 수 있지.")
        else:
            st.write("Q: 세계사적으로 어떤 독창성이 있나요?\n\n**A:** 세계의 다른 유산과 비교해도 나처럼 보존 철학이 뚜렷하고 정교한 기록을 유지하는 경우는 드물어. 우리 민족의 실력이 세계 수준이었음을 증명한단다.")

        # 탐방 기획안
        st.write("---")
        st.subheader("🗺️ 테마 탐방 기획안")
        st.success(f"**- 제목:** '{user_in}' 전문가와 함께 떠나는 {data['title']} 깊이 읽기")
        st.write("**- 필수 관람 포인트:** 외형보다는 제작 동기와 기록된 팩트의 세부 내용을 분석하며, 과거의 기술이 현대 사회에 주는 메시지를 메모하세요.")
