import streamlit as st
import requests
import urllib.parse
import random

# --- 1. 진로/관심 분야별 팩트 기반 문화유산 매핑 ---
# 이 데이터는 해당 유산이 왜 해당 진로와 관련 있는지 '역사적 팩트'를 담고 있습니다.
RELATION_DB = {
    "의학": [
        {"heritage": "동의보감", "fact": "2009년 유네스코 세계기록유산 등재. 허준이 편찬한 의학서로 당시 동양 의학 지식을 집대성한 실증적 자료입니다."},
        {"heritage": "향약구급방", "fact": "고려 시대 우리 땅의 약재로 병을 고치는 법을 정리한 현존 최고의 의학서입니다."},
        {"heritage": "제중원", "fact": "우리나라 최초의 근대식 국립 서양식 병원으로, 전통 의학에서 현대 의학으로 넘어가는 가교 역할을 했습니다."}
    ],
    "작가/출판": [
        {"heritage": "해인사 대장경판", "fact": "팔만대장경은 8만여 장의 목판에 오자 하나 없이 완벽한 편집과 기록을 보여주는 인쇄 문화의 정수입니다."},
        {"heritage": "직지심체요절", "fact": "세계에서 가장 오래된 금속 활자본으로, 지식의 대중화와 인쇄 기술 혁명을 보여주는 증거입니다."},
        {"heritage": "조선왕조실록", "fact": "사관들이 왕의 행적을 기록한 역사서로, 철저한 기록 정신과 객관적인 집필 방식을 보여줍니다."}
    ],
    "미술/디자인": [
        {"heritage": "고려청자", "fact": "독창적인 상감 기법과 비색을 통해 당시 세계 최고의 공예 예술적 성취를 증명합니다."},
        {"heritage": "백자 달항아리", "fact": "절제된 곡선의 아름다움과 담백한 색채로 한국적 미학의 극치를 보여주는 유산입니다."},
        {"heritage": "금동미륵보살반가사유상", "fact": "신라 시대 금동 조각 기술과 온화한 미소를 담은 예술적 비례가 특징입니다."}
    ],
    "과학/IT": [
        {"heritage": "첨성대", "fact": "신라 시대 천문 관측 시설로, 하늘의 데이터를 수집하고 이를 농업과 정치에 활용한 고대 과학의 산물입니다."},
        {"heritage": "자격루", "fact": "세종 시대 만든 자동 물시계로, 정밀한 기계 공학과 자동 제어 시스템이 적용된 혁신적 기구입니다."},
        {"heritage": "거중기", "fact": "정약용이 도르래 원리를 이용해 만든 건축 기계로, 수원 화성 축조의 과학적 효율성을 입증합니다."}
    ],
    "요리/식품": [
        {"heritage": "수라간", "fact": "조선 왕실의 음식을 조리하던 곳으로, 당시의 식재료 관리와 전통 조리법이 체계적으로 보존된 장소입니다."},
        {"heritage": "징광 옹기", "fact": "발효 음식 보존을 위한 숨 쉬는 그릇으로, 선조들의 식품 보관 과학이 담겨 있습니다."}
    ]
}

HEADERS = {'User-Agent': 'PerformanceBot/3.0'}

def get_wiki_summary(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

# --- 2. 웹 설정 및 CSS (팝업 하트 애니메이션) ---
st.set_page_config(page_title="역사 수행평가 전문가 AI", layout="wide")

st.markdown("""
    <style>
    @keyframes heartbeat {
        0% { transform: scale(1); }
        30% { transform: scale(1.4); }
        100% { transform: scale(1); }
    }
    .heart-active {
        display: inline-block;
        font-size: 70px;
        animation: heartbeat 0.4s ease-in-out;
        cursor: pointer;
        text-align: center;
        width: 100%;
    }
    .heart-static {
        display: inline-block;
        font-size: 70px;
        cursor: pointer;
        text-align: center;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바: 팝업 하트 ---
with st.sidebar:
    st.header("💖 응원 하트")
    if 'pop_trigger' not in st.session_state: st.session_state.pop_trigger = False
    
    if st.button("하트 꾹! ❤️"):
        st.session_state.pop_trigger = True
    else:
        st.session_state.pop_trigger = False

    # 애니메이션 클래스 적용
    heart_class = "heart-active" if st.session_state.pop_trigger else "heart-static"
    st.markdown(f'<div class="{heart_class}">❤️</div>', unsafe_allow_html=True)
    st.write("응원 하트를 누르면 힘이 납니다!")

# --- 4. 메인 화면 로직 ---
st.title("📜 진로 맞춤형 문화유산 탐구 가이드")
st.write("나의 진로/관심사를 입력하면 **역사적 팩트가 일치하는 유산**을 연결해 드립니다.")

if 'current_res' not in st.session_state: st.session_state.current_res = None

user_interest = st.text_input("나의 진로나 관심 분야 (예: 의학, 작가, 미술, IT, 요리)", placeholder="의학")

c1, c2 = st.columns([1, 4])

with c1:
    if st.button("🔍 팩트 기반 추천"):
        if user_interest:
            # 1. DB에서 매칭되는 카테고리 찾기
            found_key = next((k for k in RELATION_DB if k in user_interest), None)
            if found_key:
                st.session_state.current_res = random.choice(RELATION_DB[found_key])
            else:
                # DB에 없으면 위키백과 직접 검색 (fallback)
                st.session_state.current_res = {"heritage": user_interest, "fact": f"{user_interest}와 관련된 역사적 자료를 탐구합니다."}
        else: st.warning("분야를 입력해주세요.")

with c2:
    if st.button("🔄 다른 유산 추천"):
        if user_interest:
            found_key = next((k for k in RELATION_DB if k in user_interest), None)
            if found_key:
                options = [o for o in RELATION_DB[found_key] if o['heritage'] != st.session_state.current_res['heritage']]
                if options: st.session_state.current_res = random.choice(options)
                else: st.info("이 분야의 추천 데이터가 하나뿐입니다!")

# --- 5. 수행평가 결과 출력 ---
if st.session_state.current_res:
    res = st.session_state.current_res
    data = get_wiki_summary(res['heritage'])
    
    if data:
        st.divider()
        st.header(f"🏛️ 추천 문화유산: {data['title']}")
        
        # [팩트 확인 섹션]
        st.subheader("✅ 진로와 관련된 명확한 팩트")
        st.success(f"**[{user_interest}]** 관심사와 관련된 역사적 근거:\n\n{res['fact']}")
        st.link_button("🌐 위키백과에서 실제 팩트 더 보기", f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(data['title'])}")

        st.write("---")
        st.subheader("💬 수행평가 심화 인터뷰")
        
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'], width=350)
            else: st.write("이미지 정보 없음")
            
        with col_txt:
            st.info(f"Q: {data['title']}님, '{user_interest}' 관점에서 당신의 제작 의도는 무엇인가요?")
            st.write(f"A: 나는 당시 {user_interest}에 대한 사회적 필요와 조상들의 기술력이 합쳐져 탄생했단다. 특히 {res['fact'][:50]}... 와 같은 역사적 사실이 나의 존재 이유를 증명하지.")

        st.info("Q: 세월을 거치며 겪은 가장 큰 역사적 시련은 무엇이었나요?")
        st.write("A: 전란의 화마 속에서도 나를 지키려 했던 우리 민족의 신념이 아니었다면, 지금 너에게 {user_interest}의 역사적 증거를 보여줄 수 없었을 거야.")

        # 관점 선택 인터뷰
        v = st.radio("인터뷰 3 관점을 선택하세요", ["비판적 관점", "융합적 관점", "비교사적 관점"])
        st.write(f"**[인터뷰 3: {v}]**")
        if "비판" in v:
            st.write("Q: 제작 과정에서 백성들의 고통이나 지배층의 권력 과시는 없었나요?\n\nA: 나의 탄생 뒤에는 수많은 백성의 노역이 있었어. 그 희생이 누구를 위한 것이었는지 비판적으로 고민해보는 게 너의 과제야.")
        elif "융합" in v:
            st.write(f"Q: 현대 {user_interest} 기술과의 공통점은?\n\nA: 나의 설계에는 현대 시스템 공학과 유사한 정밀함과 선조들의 융합적 지혜가 숨어있어 과학적 가치를 더해준단다.")
        else:
            st.write("Q: 세계의 다른 유산과 비교했을 때 당신만의 독창성은?\n\nA: 세계 어디에도 나처럼 정교한 제작 방식과 보존 철학을 동시에 갖춘 유산은 드물어. 우리 민족의 독보적 실력을 보여준단다.")

        st.divider()
        st.subheader("🗺️ 테마 탐방 기획안")
        st.write(f"**- 기획 제목:** {user_interest}의 시선으로 바라본 '{data['title']}'의 팩트 탐험")
        st.write(f"**- 필수 관람 포인트:** 유산의 외형보다는 그것이 만들어진 '공정'과 '목적'에 집중하세요. 특히 {user_interest}적 가치가 실제 유물에 어떻게 투영되었는지 확인하는 것이 핵심입니다.")
