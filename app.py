import streamlit as st
import requests
import random

# --- 1. 위키백과 검색 및 상세 정보 가져오기 ---
def search_heritage(keyword):
    # 키워드로 위키백과 문서 리스트 검색
    search_url = "https://ko.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": keyword + " 문화유산 문화재",
        "format": "json",
        "srlimit": 10
    }
    res = requests.get(search_url).json()
    search_results = res.get('query', {}).get('search', [])
    return [item['title'] for item in search_results]

def get_wiki_details(title):
    # 문서 제목으로 요약 정보 가져오기
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    res = requests.get(url, headers={'User-Agent': 'SchoolHelper/1.0'})
    return res.json() if res.status_code == 200 else None

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="수행평가 가이드 AI", page_icon="🏛️", layout="wide")

# --- 3. 사이드바: 사라지는 사과 게임 ---
with st.sidebar:
    st.header("🍎 재미 요소: 사과 먹기")
    if 'apple_step' not in st.session_state:
        st.session_state.apple_step = 0
    
    apple_stages = [
        "🍎 (신선한 사과)", 
        "🍎 (아삭! 한입)", 
        "🍎 (점점 사라짐)", 
        "🍎 (거의 다 먹음)", 
        "🍏 (심지만 남음)", 
        "✨ (새 사과 등장!)"
    ]
    
    st.title(apple_stages[st.session_state.apple_step])
    if st.button("사과 한입 베어물기"):
        st.session_state.apple_step = (st.session_state.apple_step + 1) % len(apple_stages)
    
    st.write("---")
    st.write("수행평가 작성이 힘들 때 사과를 드세요!")

# --- 4. 메인 로직 ---
st.title("📜 문화유산 탐구 글쓰기 AI 도우미")
st.write("사용자의 관심사를 입력하면 적절한 문화유산을 추천하고 수행평가 답변을 생성합니다.")

# 세션 상태 초기화 (추천 결과 유지용)
if 'current_heritage' not in st.session_state:
    st.session_state.current_heritage = None

user_interest = st.text_input("나의 진로나 관심사를 입력하세요", placeholder="예: 미술, 과학, 의학, 전쟁, 요리 등")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("문화유산 추천받기"):
        if user_interest:
            results = search_heritage(user_interest)
            if results:
                st.session_state.current_heritage = random.choice(results)
            else:
                st.error("관련된 문화유산을 찾지 못했습니다.")
        else:
            st.warning("관심사를 먼저 입력해주세요.")

with col2:
    if st.button("다른 유산 추천받기 🔄"):
        if user_interest:
            results = search_heritage(user_interest)
            if results:
                # 현재와 다른 유산 선택
                new_choice = random.choice(results)
                st.session_state.current_heritage = new_choice
        else:
            st.warning("관심사를 먼저 입력해주세요.")

# --- 5. 수행평가 내용 표시 (이미지 양식 반영) ---
if st.session_state.current_heritage:
    data = get_wiki_details(st.session_state.current_heritage)
    
    if data:
        st.divider()
        st.header(f"💎 추천 문화유산: {data['title']}")
        
        # [이미지 양식: 기본 정보]
        st.subheader("📍 [기본 정보]")
        col_a, col_b = st.columns([1, 2])
        with col_a:
            if 'thumbnail' in data:
                st.image(data['thumbnail']['source'], caption=data['title'])
        with col_b:
            st.write(f"**- 선정 이유:** 저의 관심사인 '{user_interest}'와 관련하여, 이 유산이 당시 사회에서 어떤 역할을 했는지 탐구하기 위해 선정함.")
            st.write(f"**- 제작 시대:** 기록에 나타난 해당 유산의 건립 시기")
            st.write(f"**- 현재 위치:** 해당 유산의 소재지(경주, 서울 등)")

        # [이미지 양식: 인터뷰 1]
        st.subheader("🎤 [인터뷰 1] 과거인들의 생활/사상/정치")
        st.info(f"Q: {data['title']}은 당시 사람들의 삶과 어떤 관계가 있었나요?")
        st.write(f"A: 나는 당시 사람들의 {user_interest}에 대한 열망을 담아 제작되었단다. 요약하자면 '{data['extract'][:150]}...' 와 같은 역사적 배경을 가지고 있지.")

        # [이미지 양식: 인터뷰 2]
        st.subheader("🎤 [인터뷰 2] 역사적 시련 또는 현재 상황")
        st.info(f"Q: 세월을 거치며 겪은 역사적 시련이나 변화는 무엇인가요?")
        st.write(f"A: 나는 전쟁이나 자연재해로 인해 훼손될 뻔한 위기도 있었지만, 많은 이들의 노력으로 현재의 모습을 유지하고 있단다. 지금은 우리 역사를 증명하는 소중한 자산이지.")

        # [이미지 양식: 인터뷰 3]
        st.subheader("🎤 [인터뷰 3] 비판적/융합적/비교사적 관점")
        viewpoint = st.selectbox("적용할 관점을 선택하세요", ["융합적 관점(과학/원리)", "비판적 관점(의문/의심)", "비교사적 관점(다른 유산과 비교)"])
        
        if viewpoint == "융합적 관점(과학/원리)":
            st.info(f"Q: 이 유산에 담긴 과학적 원리나 현대 기술과의 연결고리는 무엇인가요?")
            st.write(f"A: 나의 구조는 단순해 보이지만, 그 안에는 치밀한 수학적 비례와 과학적 공법이 숨어 있어 현대인들도 놀라워하는 융합적 가치를 지니고 있단다.")
        elif viewpoint == "비판적 관점(의문/의심)":
            st.info(f"Q: 이 유산을 만들기 위해 당시 백성들이나 사회가 치른 희생은 없었나요?")
            st.write(f"A: 화려한 모습 뒤에는 수많은 장인과 백성들의 노역이 있었음을 잊지 말아야 해. 누구의 권력을 위해 내가 만들어졌는지 비판적으로 바라보는 시각도 중요하단다.")
        else:
            st.info(f"Q: 다른 나라의 비슷한 문화유산과 비교했을 때 당신만의 특징은 무엇인가요?")
            st.write(f"A: 나는 다른 문화권의 유산과는 차별화된 우리 민족 고유의 독창성을 가지고 있어. 비슷한 형태라도 재료나 배치 면에서 독특한 미를 보여주지.")

        # [이미지 양식: 탐방 기획안]
        st.subheader("🗺️ [선정 문화유산 테마 탐방 기획]")
        st.success(f"**- 탐방 제목:** '{user_interest}'의 시선으로 걷는 {data['title']} 여행")
        st.write(f"**- 필수 관람 포인트:** 유산의 세부 조각이나 구조를 면밀히 살피며, 당시 제작자가 가졌을 고민과 '{user_interest}'적 가치를 현장에서 직접 확인해 보세요.")

st.sidebar.markdown("---")
st.sidebar.caption("※ 본 서비스는 수행평가 초안 작성을 돕는 도구입니다. 실제 제출 시에는 내용을 본인의 말투로 다듬어 주세요.")
