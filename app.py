import streamlit as st
import requests
import urllib.parse
import re

# --- 1. 위키백과 실시간 데이터 추출 함수 ---
def fetch_heritage_by_interest(interest):
    """사용자 관심사로 위키백과를 검색해 가장 관련 있는 한국 문화유산을 찾음"""
    search_url = "https://ko.wikipedia.org/w/api.php"
    # 한국 문화유산으로 한정하기 위해 검색어 조합 최적화
    query = f"{interest} 관련 한국 문화재 유산"
    
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 5
    }
    headers = {'User-Agent': 'FactCheckBot/2.0'}
    
    try:
        res = requests.get(search_url, params=params, headers=headers).json()
        search_results = res.get('query', {}).get('search', [])
        if not search_results:
            return None
        # 가장 검색 순위가 높은 제목 반환
        return search_results[0]['title']
    except:
        return None

def get_detailed_fact(title):
    """위키백과 API에서 실제 역사적 팩트(요약문)를 가져옴"""
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    res = requests.get(url, headers={'User-Agent': 'FactCheckBot/2.0'})
    return res.json() if res.status_code == 200 else None

# --- 2. 웹 페이지 설정 및 하트 애니메이션 CSS ---
st.set_page_config(page_title="실시간 팩트체크 수행 AI", layout="wide")

st.markdown("""
    <style>
    @keyframes heartbeat {
        0% { transform: scale(1); }
        25% { transform: scale(1.4); }
        50% { transform: scale(1); }
        75% { transform: scale(1.4); }
        100% { transform: scale(1); }
    }
    .heart-active {
        display: inline-block;
        font-size: 80px;
        animation: heartbeat 0.6s ease-in-out;
        cursor: pointer;
        text-align: center;
        width: 100%;
    }
    .heart-static {
        display: inline-block;
        font-size: 80px;
        text-align: center;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바: 팝업 하트 ---
with st.sidebar:
    st.header("💖 응원 하트")
    if 'pop' not in st.session_state: st.session_state.pop = False
    
    if st.button("하트 클릭! ❤️"):
        st.session_state.pop = True
    else:
        st.session_state.pop = False

    h_class = "heart-active" if st.session_state.pop else "heart-static"
    st.markdown(f'<div class="{h_class}">❤️</div>', unsafe_allow_html=True)
    st.write("하트가 두근두근 커졌다 작아집니다!")

# --- 4. 메인 로직: 실시간 분석 ---
st.title("🇰🇷 실시간 분석형 문화유산 인터뷰 AI")
st.write("관심사를 입력하면 위키백과에서 **실제 데이터**를 찾아 유산을 추천하고 인터뷰를 만듭니다.")

user_input = st.text_input("나의 진로/관심 분야 (예: 심리학, 인공지능, 기상학, 환경 등)", placeholder="입력 후 엔터를 누르세요")

if user_input:
    with st.spinner(f"'{user_input}'와(과) 관련된 한국 문화유산을 실시간 탐색 중..."):
        # 1. 실시간 검색으로 유산 제목 결정
        target_title = fetch_heritage_by_interest(user_input)
        
        if target_title:
            # 2. 유산의 실제 팩트 정보 가져오기
            data = get_detailed_fact(target_title)
            
            if data and 'extract' in data:
                st.divider()
                st.header(f"🏛️ 실시간 추천 유산: {data['title']}")
                
                # 팩트 근거 (연관성 설명)
                st.subheader("✅ 팩트 기반 연관성 분석")
                # 위키백과 요약문에서 팩트 추출
                fact_text = data['extract']
                st.info(f"**'{user_input}'** 분야와 **{data['title']}**의 연결고리:\n\n이 유산은 역사적으로 '{fact_text[:120]}...'와 같은 특징을 지니고 있어, {user_input}적 관점에서 탐구하기에 매우 적합한 팩트를 담고 있습니다.")
                st.link_button("🌐 위키백과 실시간 원문 데이터 확인", data['content_urls']['desktop']['page'])

                st.write("---")
                st.subheader("💬 수행평가용 실시간 팩트 인터뷰")

                col_img, col_txt = st.columns([1, 2])
                with col_img:
                    if 'thumbnail' in data: st.image(data['thumbnail']['source'], caption=data['title'], use_container_width=True)
                
                with col_txt:
                    # 인터뷰 1: 실제 팩트 기반 정체성
                    st.write(f"**[인터뷰 1: 나의 가치]**")
                    st.write(f"Q: {data['title']}님, '{user_input}' 관점에서 당신은 어떤 존재인가요?")
                    # 위키백과 데이터 활용한 답변 생성
                    st.write(f"A: 나는 '{fact_text[:150]}...'라는 역사적 기록이 증명하듯, 당시 사람들의 기술과 지혜가 집약된 결과물이란다. {user_input}의 본질과 나의 탄생 배경은 맞닿아 있지.")

                # 인터뷰 2: 실제 팩트 기반 시련 (데이터 내 연도나 전란 키워드 추출 시도)
                st.write("**[인터뷰 2: 역사적 기록 속 시련]**")
                st.write("Q: 당신의 기록 중 가장 기억에 남는 실제 역사적 변화나 시련은 무엇인가요?")
                
                # 팩트 기반 시련 답변 구성 (전쟁, 훼손, 복원 등의 단어가 있는지 확인)
                trial_msg = "오랜 세월을 거치며 시대의 변화와 함께 훼손되기도 했지만, 우리 민족의 복원 의지 덕분에 지금의 자리를 지킬 수 있었어."
                if "전쟁" in fact_text or "란" in fact_text:
                    trial_msg = "역사 기록에 남은 전란의 화마 속에서도 내 가치를 알아본 이들이 나를 지켜냈기에 지금 너와 만날 수 있는 거란다."
                elif "도굴" in fact_text or "보수" in fact_text:
                    trial_msg = "과거 보수 과정에서 새로운 유물이 발견되거나 훼손을 극복한 사례는 내 생애 가장 큰 변화의 순간이었지."
                
                st.write(f"A: {trial_msg} 팩트 중심의 기록을 보면 내가 견뎌온 시간의 깊이를 알 수 있을 거야.")

                # 인터뷰 3: 관점 선택
                st.write("---")
                v = st.radio("질문 관점을 선택하세요", ["융합적 관점", "비판적 관점", "비교사적 관점"])
                st.write(f"**[인터뷰 3: {v}]**")
                if "융합" in v:
                    st.write(f"Q: 현대 {user_input} 기술과 당신의 제작 원리 사이의 공통점은?\n\nA: 나의 제작 방식에는 단순한 예술을 넘어 치밀한 과학적 계산이 숨어있어. 조상들의 융합적 사고가 얼마나 현대적인지 팩트로 증명해줄게.")
                elif "비판" in v:
                    st.write("Q: 당신을 만들기 위해 치렀던 사회적 비용이나 백성들의 희생에 대한 생각은?\n\nA: 나의 가치를 칭송할 때, 나를 세우기 위해 고된 노역을 견뎠던 민초들의 땀방울도 함께 기억해줘. 그것이 진정한 역사적 성찰이란다.")
                else:
                    st.write("Q: 다른 나라의 비슷한 유산과 비교했을 때 당신만의 독창성은?\n\nA: 세계 어디에도 나처럼 자연과 조화를 이루면서도 정교한 기록과 철학을 동시에 유지하는 유산은 드물어. 이것이 한국 문화유산만의 자부심이지.")

                # 탐방 기획안
                st.divider()
                st.subheader("🗺️ 테마 탐방 기획안")
                st.success(f"**- 제목:** {user_interest if 'user_interest' in locals() else user_input}의 눈으로 분석한 '{data['title']}' 팩트 투어")
                st.write(f"**- 필수 관람 포인트:** 위키백과에서 확인한 '{data['title']}'의 핵심 구조를 눈으로 직접 확인하고, 안내판의 역사적 설명과 실제 모습의 일치 여부를 대조하며 감상하세요.")
            else:
                st.error("상세 정보를 가져오는 데 실패했습니다. 다른 유산으로 시도해보세요.")
        else:
            st.error(f"'{user_input}'와(과) 관련된 한국 문화유산을 찾을 수 없습니다. 조금 더 넓은 범위의 단어를 입력해보세요.")
