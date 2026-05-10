import streamlit as st
import requests
import random

# 공통 헤더 (위키백과 API 권장 사항)
HEADERS = {
    'User-Agent': 'HeritageProjectAI/1.0 (contact: your-email@example.com)'
}

# 1. 위키백과 검색 함수 (에러 수정됨)
def search_heritage(keyword):
    search_url = "https://ko.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": keyword + " 문화재", # 검색어 최적화
        "format": "json",
        "srlimit": 20 # 더 많은 후보를 가져옴
    }
    try:
        # params=search_params와 headers를 반드시 포함해야 합니다.
        res = requests.get(search_url, params=search_params, headers=HEADERS)
        res.raise_for_status() # HTTP 에러 체크
        data = res.json()
        search_results = data.get('query', {}).get('search', [])
        return [item['title'] for item in search_results]
    except Exception as e:
        st.error(f"검색 중 오류가 발생했습니다: {e}")
        return []

# 2. 위키백과 상세 정보 가져오기
def get_wiki_details(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

# --- UI 설정 ---
st.set_page_config(page_title="역사 수행평가 AI", page_icon="🏛️")

# --- 사이드바: 사라지는 사과 게임 ---
with st.sidebar:
    st.header("🍎 사과 게임")
    if 'apple_step' not in st.session_state:
        st.session_state.apple_step = 0
    
    # 사과의 5단계 상태 (점점 작아짐)
    apple_icons = ["🍎", "🍎 (아삭!)", "🍎 (우걱우걱)", "🍏 (심지만 남음)", "✨ (사과 탄생!)"]
    st.title(apple_icons[st.session_state.apple_step])
    
    if st.button("사과 한입 먹기"):
        st.session_state.apple_step = (st.session_state.apple_step + 1) % len(apple_icons)
    st.write("사과가 다 사라지면 다시 생겨요!")

# --- 메인 화면 ---
st.title("📜 문화유산 탐구 글쓰기 도우미")
st.write("진로나 관심사(예: 미술, 의학)를 입력하면 최적의 문화유산을 추천해 드립니다.")

# 세션 상태 관리 (추천 리스트 유지)
if 'heritage_list' not in st.session_state:
    st.session_state.heritage_list = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = -1

# 관심사 입력
user_interest = st.text_input("나의 진로나 관심사를 말해주세요", placeholder="예: 미술, 건축, 전쟁, 과학 등")

c1, c2 = st.columns(2)

with c1:
    if st.button("🔍 관련 유산 추천받기"):
        if user_interest:
            with st.spinner("유산을 찾는 중..."):
                results = search_heritage(user_interest)
                if results:
                    st.session_state.heritage_list = results
                    st.session_state.current_index = 0 # 첫 번째 추천
                else:
                    st.error("관련 유산을 찾지 못했습니다. 다른 단어로 입력해보세요.")
        else:
            st.warning("관심사를 먼저 입력해주세요.")

with c2:
    if st.button("🔄 다른 유산으로 바꿀래"):
        if st.session_state.heritage_list:
            # 다음 유산으로 넘기기
            st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.heritage_list)
        else:
            st.warning("먼저 추천받기 버튼을 눌러주세요.")

# --- 수행평가 양식 출력 ---
if st.session_state.current_index != -1:
    target_title = st.session_state.heritage_list[st.session_state.current_index]
    data = get_wiki_details(target_title)
    
    if data:
        st.divider()
        st.header(f"💎 선정된 문화유산: {data['title']}")
        
        # [이미지 양식: 기본 정보]
        st.subheader("📍 [1. 기본 정보]")
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if 'thumbnail' in data:
                st.image(data['thumbnail']['source'])
        with col_info:
            st.write(f"**- 선정 이유:** 평소 저의 관심사인 '{user_interest}'의 관점에서 이 유산에 담긴 역사적 가치와 특징을 깊이 있게 이해하고 싶어 선정했습니다.")
            st.write(f"**- 제작 시대:** {data.get('description', '역사 기록 참조')}")
            st.write(f"**- 현재 위치:** 대한민국 소재지 (상세 위치 검색 권장)")

        # [이미지 양식: 인터뷰 1]
        st.subheader("🎤 [2. 인터뷰 1] 과거인의 삶/사상/정치")
        st.info(f"Q: {data['title']}님, 당신은 당시 사람들에게 어떤 존재였나요?")
        st.write(f"A: 나는 당시 {user_interest}적 가치를 중요하게 여기던 사람들의 열망으로 탄생했어. 나의 모습에는 '{data['extract'][:120]}...' 와 같은 시대적 상황과 사상이 깃들어 있단다.")

        # [이미지 양식: 인터뷰 2]
        st.subheader("🎤 [3. 인터뷰 2] 역사적 시련/변화")
        st.info(f"Q: 오랜 세월을 지내며 겪은 가장 큰 시련은 무엇이었나요?")
        st.write(f"A: 수많은 전쟁과 기상 변화를 겪으며 훼손될 뻔하기도 했지만, 우리 민족의 노력으로 지금의 자리를 지킬 수 있었어. 지금은 너희들과 역사를 이어주는 통로 역할을 하고 있지.")

        # [이미지 양식: 인터뷰 3]
        view = st.radio("인터뷰 3의 관점을 선택하세요", ["융합적(과학/원리)", "비판적(의문/희생)", "비교사적(타 유산과 비교)"])
        st.subheader(f"🎤 [4. 인터뷰 3] {view}")
        
        if "융합" in view:
            st.info(f"Q: 당신 속에 숨겨진 과학적 원리는 무엇인가요?")
            st.write(f"A: 겉으로는 예술적이지만, 나의 구조 안에는 치밀한 수학적 계산과 조상들의 공학적 지혜가 융합되어 있어 현대 기술로도 감탄할 만한 원리가 숨겨져 있단다.")
        elif "비판" in view:
            st.info(f"Q: 당신을 만들기 위해 희생된 사람들은 없었나요?")
            st.write(f"A: 나의 화려함 뒤에는 당시 수많은 백성들의 고된 노역과 눈물이 있었음을 잊지 말아줘. 누구를 위해 내가 세워졌는지 고민해보는 시간도 필요해.")
        else:
            st.info(f"Q: 다른 나라의 유산과 비교했을 때 당신만의 매력은?")
            st.write(f"A: 나는 외국 유산들과는 다른, 우리 민족 특유의 선의 아름다움과 절제미를 가지고 있어. 재료의 선택부터 배치까지 독창적인 한국적 미를 보여주지.")

        # [이미지 양식: 탐방 기획안]
        st.subheader("🗺️ [5. 테마 탐방 기획안]")
        st.success(f"**- 제목:** '{user_interest}'의 시선으로 바라본 {data['title']} 탐방 기획")
        st.write(f"**- 필수 관람 포인트:** 유산의 외형뿐만 아니라 세부적인 디테일을 '{user_interest}'적 관점에서 분석하며 감상하세요. 당시 사람들이 어떤 마음으로 이 유산을 빚었을지 상상하는 것이 핵심입니다.")

st.sidebar.markdown("---")
st.sidebar.caption("※ API 오류 방지를 위해 검색 로직을 보강했습니다.")
