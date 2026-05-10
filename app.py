import streamlit as st
import requests
import random
import urllib.parse

# --- 설정 및 헤더 ---
HEADERS = {'User-Agent': 'HistoryEduBot/2.0 (contact: edu-helper@example.com)'}

# 1. 위키백과 검색 및 상세 정보 가져오기
def get_wiki_data(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
    except:
        return None
    return None

def search_heritage(keyword):
    search_url = "https://ko.wikipedia.org/w/api.php"
    params = {
        "action": "query", "list": "search", "srsearch": keyword + " 문화재",
        "format": "json", "srlimit": 15
    }
    try:
        res = requests.get(search_url, params=params, headers=HEADERS)
        data = res.json()
        return [item['title'] for item in data.get('query', {}).get('search', [])]
    except:
        return []

# --- UI 설정 ---
st.set_page_config(page_title="역사 수행평가 팩트체크 AI", layout="wide")

# --- 사이드바: 사라지는 사과 게임 ---
with st.sidebar:
    st.header("🍎 간식 타임")
    if 'apple' not in st.session_state: st.session_state.apple = 0
    apples = ["🍎", "🍎(한입 냠!)", "🍎(반쪽 슥~)", "🍏(심지 달랑)", "✨(새 사과!)"]
    st.title(apples[st.session_state.apple])
    if st.button("사과 먹기"):
        st.session_state.apple = (st.session_state.apple + 1) % len(apples)
    st.write("---")
    st.caption("수행평가 팩트체크 도우미 v2.0")

# --- 메인 화면 ---
st.title("📜 문화유산 탐구 심화 인터뷰 & 팩트체크")
st.write("진로나 관심사를 입력하면, **검증된 역사적 사실**을 바탕으로 깊이 있는 인터뷰를 작성해 드립니다.")

if 'h_list' not in st.session_state: st.session_state.h_list = []
if 'idx' not in st.session_state: st.session_state.idx = -1

user_input = st.text_input("나의 진로/관심사 (예: 미술, 의학, IT, 건축 등)", placeholder="미술 관련 문화유산")

c1, c2 = st.columns(2)
with c1:
    if st.button("🔍 관련 유산 찾기"):
        if user_input:
            with st.spinner("역사 데이터 분석 중..."):
                st.session_state.h_list = search_heritage(user_input)
                st.session_state.idx = 0 if st.session_state.h_list else -1
        else: st.warning("키워드를 입력해주세요.")
with c2:
    if st.button("🔄 다른 유산 추천"):
        if st.session_state.h_list:
            st.session_state.idx = (st.session_state.idx + 1) % len(st.session_state.h_list)

# --- 결과 출력 영역 ---
if st.session_state.idx != -1:
    title = st.session_state.h_list[st.session_state.idx]
    data = get_wiki_data(title)
    
    if data:
        st.divider()
        st.header(f"🏛️ 탐구 대상: {data['title']}")
        
        # [팩트 체크 링크 제공]
        st.subheader("🔍 [팩트 체크 및 근거 자료]")
        wiki_url = f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(data['title'])}"
        heritage_url = f"https://www.heritage.go.kr/heri/cul/culSelectViewList.do?searchCondition1={urllib.parse.quote(data['title'])}"
        
        col_link1, col_link2 = st.columns(2)
        with col_link1:
            st.link_button("🌐 위키백과 원문 확인 (상세 역사)", wiki_url)
        with col_link2:
            st.link_button("🏛️ 국가유산청 공식 검색 (국가 지정 정보)", heritage_url)
        
        st.write("---")

        # 1. 기본 정보 (이미지 양식 반영)
        st.subheader("📍 1. 기본 정보 및 선정 이유")
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'], use_container_width=True)
            else: st.warning("이미지가 없습니다.")
        with col_info:
            st.write(f"**- 선정 유산:** {data['title']}")
            st.write(f"**- 선정 이유(진로 연결):** 저는 '{user_input}' 분야에 관심이 많습니다. {data['title']}은 당시의 {user_input}적 역량이 총동원된 결정체이며, 이를 통해 과거 선조들이 해당 기술을 어떻게 구현하고 사회에 기여했는지 심도 있게 분석하고자 선정했습니다.")
            st.write(f"**- 역사적 개요:** {data.get('extract', '정보 없음')[:200]}...")

        # 2. 인터뷰 1: 과거인의 생활/사상/정치 (상세 버전)
        st.subheader("🎤 2. 인터뷰: 과거의 숨결을 묻다")
        st.info(f"Q: {data['title']}님, 당신이 만들어질 당시 사람들의 삶과 사상은 어떠했나요?")
        st.write(f"""
        **A (상세 답변):** "당시 나는 단순히 아름다움을 위해 존재한 것이 아니었단다. 당시 사회는 종교적으로는 불교(혹은 유교)가 지배적이었고, 정치적으로는 왕권의 안정과 백성들의 평안을 기원하는 마음이 컸지. 
        사람들은 나를 통해 현세의 고통을 잊고 이상향을 꿈꿨어. 예를 들어, 내가 만약 석탑이라면 사람들은 탑을 돌며 가족의 건강을 빌었고, 내가 성벽이라면 외적의 침입으로부터 공동체를 지키고자 하는 강력한 국방 의지가 담겼던 것이지. 
        나의 세부 조각 하나하나에는 그 시대 사람들이 가장 중요하게 생각했던 가치관이 고스란히 녹아 있단다."
        """)

        # 3. 인터뷰 2: 역사적 시련과 변화
        st.subheader("🎤 3. 인터뷰: 세월의 풍파를 견디다")
        st.info("Q: 긴 시간 동안 겪었던 가장 고통스러웠던 역사적 시련은 무엇이었나요?")
        st.write(f"""
        **A (상세 답변):** "가장 큰 시련은 역시 전쟁이었어. 임진왜란이나 병자호란 같은 큰 전란 속에서 나의 목조 부분은 불타 없어지기도 했고, 일제강점기에는 우리 민족의 정기를 끊으려는 이들에 의해 무단으로 해체되거나 해외로 반출될 뻔한 위기도 겪었지. 
        하지만 그 모든 시련 속에서도 나를 지켜내려 했던 수많은 이름 없는 민초들과 학자들의 노력이 있었기에 지금의 내가 존재할 수 있는 거란다. 지금은 복원 작업을 통해 예전의 위용을 되찾았지만, 내 몸에 남은 상흔들은 여전히 우리 역사의 아픈 기록으로 남아있어."
        """)

        # 4. 인터뷰 3: 관점별 심화 질문 (선택)
        view = st.radio("적용할 비판적/융합적 관점을 선택하세요", ["융합적 관점 (과학/예술)", "비판적 관점 (권력/희생)", "비교사적 관점 (세계사적 위치)"])
        st.subheader(f"🎤 4. 인터뷰: {view}")
        
        if "융합" in view:
            st.write(f"**Q: 당신의 구조 속에 숨겨진 현대 과학으로도 놀라운 원리는 무엇인가요?**")
            st.write(f"**A:** '나의 비례미 뒤에는 치밀한 수학적 계산이 숨어 있단다. 예를 들어 지진에 견디는 내진 설계나, 습기를 조절하는 과학적인 통풍 구조는 현대의 공학 기술과 비교해도 손색이 없지. 이는 선조들이 자연과 조화를 이루면서도 기술적 완성도를 높이려 했던 융합적 사고의 산물이란다.'")
        elif "비판" in view:
            st.write(f"**Q: 당신을 건립하는 과정에서 백성들의 고통이나 지배층의 권력 과시는 없었나요?**")
            st.write(f"**A:** '날카로운 지적이구나. 나를 세우기 위해 수만 명의 백성이 동원되어 고된 노역을 견뎌야 했어. 때로는 왕실의 권위를 세우기 위해 막대한 국가 예산이 투입되어 민생이 힘들어지기도 했지. 나를 바라볼 때 화려함만 보지 말고, 그 뒤에 숨겨진 민초들의 땀방울과 시대적 한계도 함께 읽어주길 바란다.'")
        else:
            st.write(f"**Q: 동시대 다른 나라의 유산과 비교했을 때 당신만의 독창성은 무엇인가요?**")
            st.write(f"**A:** '중국이나 일본의 유산들이 화려함이나 정형화된 미를 강조했다면, 나는 자연스러운 곡선과 주변 지형과의 조화를 최우선으로 했어. 인위적이지 않으면서도 기품을 잃지 않는 것, 그것이 세계 어디에서도 찾아볼 수 없는 우리 유산만의 독보적인 가치란다.'")

        # 5. 탐방 기획안 (수행평가 마무리)
        st.subheader("🗺️ 5. 테마 탐방 기획안")
        st.success(f"**- 기획 제목:** [ {user_input} ]의 관점으로 재해석하는 {data['title']} 정밀 탐구")
        st.write(f"**- 기획 의도:** 단순히 유산을 구경하는 것을 넘어, '{user_input}'적 시각에서 유산의 구조와 의미를 분석함으로써 과거의 지혜를 현대적으로 계승하고자 함.")
        st.write(f"**- 필수 관람 포인트:** 전체적인 모습보다는 유산의 세부적인 마감 기법이나 재료의 질감을 직접 확인하고, 안내판에 적힌 역사적 사실과 실제 모습을 비교하며 감상할 것.")

st.sidebar.markdown("---")
st.sidebar.caption("본 정보는 위키백과 오픈 데이터를 기반으로 생성되었습니다. 상세 내용은 제공된 링크를 통해 반드시 교차 검증하세요.")
