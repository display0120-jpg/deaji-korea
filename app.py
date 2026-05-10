import streamlit as st
import requests
import urllib.parse
import random

# --- 위키백과 API 함수 (실시간 검색 및 추천용) ---
def search_heritage_by_ai(interest):
    """사용자 관심사 키워드로 위키백과에서 한국의 문화유산을 검색하여 리스트 반환"""
    search_url = "https://ko.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{interest} 한국 문화재 유산", # 키워드 조합으로 검색 범위 확대
        "format": "json",
        "srlimit": 15
    }
    headers = {'User-Agent': 'SchoolProjectBot/2.0'}
    try:
        res = requests.get(search_url, params=params, headers=headers)
        data = res.json()
        results = data.get('query', {}).get('search', [])
        # 제목 리스트만 추출
        return [item['title'] for item in results]
    except:
        return []

def get_detailed_info(title):
    """선정된 유산의 상세 설명과 이미지를 가져옴"""
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    res = requests.get(url, headers={'User-Agent': 'SchoolProjectBot/2.0'})
    return res.json() if res.status_code == 200 else None

# --- 설정 및 CSS (하트 무한 성장 애니메이션) ---
st.set_page_config(page_title="AI 역사 수행평가 도우미", layout="wide")

# 하트 크기가 누를 때마다 커지도록 세션 상태 관리
if 'heart_size' not in st.session_state:
    st.session_state.heart_size = 1.0

# 하트 스타일 적용
st.markdown(f"""
    <style>
    .growing-heart {{
        display: inline-block;
        font-size: 50px;
        transform: scale({st.session_state.heart_size});
        transition: transform 0.2s ease-in-out;
        cursor: pointer;
        text-align: center;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바: 무한 성장 하트 ---
with st.sidebar:
    st.header("💖 응원 하트")
    st.write("누를 때마다 하트가 커져요!")
    
    if st.button("하트 키우기 ❤️"):
        st.session_state.heart_size += 0.2  # 클릭당 0.2배씩 커짐
        
    # 하트 출력
    st.markdown(f'<div class="growing-heart">❤️</div>', unsafe_allow_html=True)
    
    if st.button("하트 초기화"):
        st.session_state.heart_size = 1.0
        st.rerun()

# --- 메인 화면 로직 ---
st.title("📜 AI 실시간 문화유산 추천 & 인터뷰 생성")
st.write("관심사(의학, IT, 미술, 요리 등)를 입력하면 위키백과 API가 관련 유산을 찾아줍니다.")

# 세션 상태 초기화
if 'heritage_results' not in st.session_state:
    st.session_state.heritage_results = []
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = -1

user_interest = st.text_input("나의 진로/관심 분야를 입력하세요", placeholder="예: 의학, 작가, 수학, 군사 등")

c1, c2 = st.columns([1, 4])

with c1:
    if st.button("🔍 AI 추천받기"):
        if user_interest:
            with st.spinner("AI가 위키백과를 검색 중..."):
                results = search_heritage_by_ai(user_interest)
                if results:
                    st.session_state.heritage_results = results
                    st.session_state.current_idx = 0
                else:
                    st.error("관련 유산을 찾지 못했습니다.")
        else:
            st.warning("분야를 입력해주세요.")

with c2:
    if st.button("🔄 다른 유산 추천 (실시간)"):
        if st.session_state.heritage_results:
            st.session_state.current_idx = (st.session_state.current_idx + 1) % len(st.session_state.heritage_results)
        else:
            st.info("먼저 추천받기 버튼을 눌러주세요.")

# --- 수행평가 양식 출력 ---
if st.session_state.current_idx != -1:
    target_title = st.session_state.heritage_results[st.session_state.current_idx]
    data = get_detailed_info(target_title)
    
    if data:
        st.divider()
        st.header(f"🏛️ AI 추천 유산: {data['title']}")
        
        # [선정 이유 및 팩트]
        st.subheader("✅ 선정 이유 및 관심사 연결")
        st.info(f"이 유산은 **'{user_interest}'** 분야와 역사적으로 밀접한 관련이 있습니다. {data.get('extract', '')[:150]}... 와 같은 역사적 배경을 바탕으로 선정하였습니다.")
        st.link_button("🌐 실시간 팩트 확인 (위키백과 링크)", f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(data['title'])}")

        st.write("---")
        st.subheader("💬 수행평가용 가상 인터뷰")
        
        col_img, col_txt = st.columns([1, 2])
        with col_img:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'], caption=data['title'])
            else: st.write("이미지 정보가 없습니다.")
        
        with col_txt:
            st.write("**[인터뷰 1: 생활과 사상]**")
            st.write(f"Q: {data['title']}님, 당신은 당시 사람들에게 어떤 존재였나요?")
            st.write(f"A: 나는 당시 {user_interest}의 발전을 갈망하던 시대적 요구에 따라 탄생했어. 나의 모습에는 당시 사회의 사상과 생활상이 고스란히 담겨 있단다.")

        st.write("**[인터뷰 2: 역사적 시련]**")
        st.write("Q: 세월을 거치며 겪은 역사적 시련은 무엇이었나요?")
        st.write("A: 전란과 약탈의 위기 속에서도 나를 지킨 건 우리 조상들의 보존에 대한 강한 신념이었어. 덕분에 지금 너에게 {user_interest}의 역사적 가치를 증명할 수 있게 되었단다.")

        # 관점 선택
        view = st.radio("인터뷰 3 관점을 선택하세요", ["융합적 관점(과학/원리)", "비판적 관점(의심/희생)", "비교사적 관점(비교)"])
        st.write(f"**[인터뷰 3: {view}]**")
        if "융합" in view:
            st.write(f"Q: 현대 {user_interest} 기술과의 공통점은?")
            st.write("A: 나의 설계에는 현대 시스템 공학과 유사한 정밀함이 숨어있어. 조상들의 융합적 지혜를 엿볼 수 있지.")
        elif "비판" in view:
            st.write("Q: 당신을 만들기 위한 희생에 대해 어떻게 생각하나요?")
            st.write("A: 나의 탄생 뒤에는 수많은 백성의 노역이 있었어. 그 희생이 누구를 위한 것이었는지 비판적으로 고민해보길 바라.")
        else:
            st.write("Q: 다른 나라의 유산과 비교했을 때 당신만의 특징은?")
            st.write("A: 세계의 다른 유산과 비교해도 나처럼 정교한 기록과 철학을 유지하는 경우는 드물어. 우리 민족의 독창적인 실력을 보여준단다.")

        # 탐방 기획안
        st.divider()
        st.subheader("🗺️ 테마 탐방 기획안")
        st.success(f"**- 제목:** '{user_interest}'의 시선으로 바라본 {data['title']} 깊이 읽기")
        st.write(f"**- 기획 의도:** 단순히 구경하는 것을 넘어, '{user_interest}'적 시각에서 유산의 의미를 분석함.")
        st.write("**- 필수 관람 포인트:** 외형보다는 제작 동기와 기록된 팩트의 세부 내용을 분석하며, 과거의 기술이 현대에 주는 메시지를 확인하세요.")
