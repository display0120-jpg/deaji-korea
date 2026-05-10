import streamlit as st
import requests
import urllib.parse

# --- 1. 관심 분야별 명확한 문화유산 매핑 데이터 (팩트 중심) ---
# 사용자가 입력한 키워드가 아래 리스트에 포함되면 해당 유산을 우선 추천합니다.
RECOMMEND_DATA = {
    "의학": {
        "heritage": "동의보감",
        "reason": "동의보감은 2009년 유네스코 세계기록유산으로 등재된 의학 서적으로, 당시 동양 의학의 지식을 집대성한 결과물입니다. 의학 전공 희망자에게는 질병 치료를 넘어 백성들을 구제하려던 '애민 정신'과 체계적인 데이터 정리법을 배울 수 있는 최고의 유산입니다.",
        "fact_link": "https://ko.wikipedia.org/wiki/동의보감"
    },
    "작가": {
        "heritage": "팔만대장경",
        "reason": "작가나 출판 분야에 관심이 있다면 목판인쇄술의 정수인 팔만대장경이 적합합니다. 8만 개가 넘는 목판에 오자 하나 없이 정교하게 새겨진 기록물로, 방대한 양의 정보를 편집하고 보존하는 기록 문화의 정수를 보여주기 때문입니다.",
        "fact_link": "https://ko.wikipedia.org/wiki/해인사_대장경판"
    },
    "건축": {
        "heritage": "수원 화성",
        "reason": "정약용의 거중기를 활용한 과학적 성곽 설계로 유명합니다. 성벽의 구조와 방어 시설이 서양과 동양의 건축술을 융합한 사례로 평가받아 건축가 지망생에게 가장 적합한 유산입니다.",
        "fact_link": "https://ko.wikipedia.org/wiki/수원_화성"
    },
    "IT": {
        "heritage": "직지심체요절",
        "reason": "세계에서 가장 오래된 금속 활자본으로, 정보의 대중화와 복제 기술의 혁신을 상징합니다. 현대의 정보 처리 및 배포 기술(IT)의 근간이 되는 '정보의 복제와 전파'를 처음으로 현실화한 기술적 유산입니다.",
        "fact_link": "https://ko.wikipedia.org/wiki/직지심체요절"
    },
    "예술": {
        "heritage": "고려청자",
        "reason": "독창적인 상감 기법과 비색을 통해 당시 세계 최고의 공예 기술을 보여줍니다. 디자인이나 미술 분야에 관심이 있다면 선과 색채의 조화, 그리고 재료학적인 우수성을 탐구하기에 최적입니다.",
        "fact_link": "https://ko.wikipedia.org/wiki/고려청자"
    }
}

HEADERS = {'User-Agent': 'SchoolHelperApp/2.0'}

def get_wiki_summary(title):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

# --- 2. 웹 설정 ---
st.set_page_config(page_title="역사 수행평가 팩트마스터", layout="wide")

# --- 3. 사이드바: 사라지는 사과 게임 (20회 클릭 이벤트) ---
with st.sidebar:
    st.header("🍎 사과 먹기 챌린지")
    if 'apple_count' not in st.session_state:
        st.session_state.apple_count = 0
    
    count = st.session_state.apple_count
    
    # 사과 상태 아이콘 (5단계 반복)
    apple_icons = ["🍎", "🍎(한입)", "🍎(반쪽)", "🍎(심지)", "✨(뿅)"]
    current_icon = apple_icons[count % 5]
    
    st.title(current_icon)
    st.write(f"현재 먹은 횟수: {count}번")

    if st.button("사과 먹기 🍎"):
        st.session_state.apple_count += 1
        st.rerun()

    # 20번 클릭 시 비밀 메시지
    if count >= 20:
        st.error("🚨 비밀 메시지 발견!")
        st.subheader("변지원 바보")
        if st.button("초기화"):
            st.session_state.apple_count = 0
            st.rerun()

# --- 4. 메인 화면 로직 ---
st.title("📜 맞춤형 문화유산 탐구 AI")
st.write("관심사(의학, 작가, 미술 등)를 입력하면 **팩트 기반의 유산**을 추천하고 수행평가 답변을 완성합니다.")

user_interest = st.text_input("나의 관심 분야를 입력하세요", placeholder="예: 의학, 작가, IT, 건축, 미술 등")

if user_interest:
    # 1. 추천 로직 (매핑 데이터 확인)
    heritage_name = ""
    reason_text = ""
    fact_url = ""

    # 키워드 포함 여부 확인
    found = False
    for key, val in RECOMMEND_DATA.items():
        if key in user_interest:
            heritage_name = val['heritage']
            reason_text = val['reason']
            fact_url = val['fact_link']
            found = True
            break
    
    # 매핑 데이터에 없으면 일반 검색
    if not found:
        st.info("정의된 키워드가 아니어서 일반 검색을 수행합니다.")
        heritage_name = user_interest + " 유산" # 임시 검색어
        reason_text = f"이 분야는 조상들의 삶 속에서 {user_interest}와 관련된 실질적인 도구와 사상으로 나타납니다."
        fact_url = f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(user_interest)}"

    # 2. 데이터 출력
    data = get_wiki_summary(heritage_name)
    
    if data:
        st.divider()
        st.header(f"🏛️ 추천 유산: {data['title']}")
        
        # [팩트 근거 섹션]
        st.subheader("✅ 팩트 체크 및 선정 근거")
        st.success(f"**{user_interest}** 분야와 관련 있는 이유:\n\n{reason_text}")
        st.link_button("🔗 팩트 확인 (위키백과 공식 링크)", fact_url)

        # [수행평가 양식 채우기]
        st.write("---")
        st.subheader("📑 수행평가 가상 인터뷰 (심화 버전)")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if 'thumbnail' in data: st.image(data['thumbnail']['source'], caption=data['title'])
        with col2:
            st.write(f"**[기본 정보]**")
            st.write(f"- 제작 시대: {data.get('description', '역사 기록 참조')}")
            st.write(f"- 선정 이유: {reason_text[:100]}...")

        # 인터뷰 1
        st.info(f"Q: {data['title']}님, 당시 사람들에게 당신은 어떤 의미였나요?")
        st.write(f"**A:** 나는 당시 사람들의 실질적인 문제를 해결하고자 하는 의지에서 태어났단다. 특히 {user_interest}에 관심이 많았던 당시 학자들과 기술자들은 나를 통해 더 나은 세상을 만들고자 했지. 나의 기록과 형태 속에는 그들의 치밀한 연구와 노력이 고스란히 팩트로 남아있어.")

        # 인터뷰 2
        st.info("Q: 역사 속에서 겪은 가장 큰 시련과 변화는 무엇인가요?")
        st.write(f"**A:** 긴 세월 동안 전란으로 인해 소실될 뻔한 위기가 가장 컸어. 하지만 우리 후손들은 나를 지키기 위해 산속 깊은 곳으로 나를 옮기거나, 목숨을 걸고 보존해왔지. 덕분에 지금은 {user_interest}의 역사적 증거로서 세계가 인정하는 가치를 지니게 되었단다.")

        # 인터뷰 3 (심화 관점)
        view = st.selectbox("인터뷰 3 관점 선택", ["융합적 관점", "비판적 관점", "비교사적 관점"])
        if view == "융합적 관점":
            st.write(f"**Q: 당신 속에 담긴 현대 {user_interest} 기술과 일맥상통하는 원리는?**")
            st.write(f"**A:** 나의 제작 과정은 현대의 시스템 설계와 매우 닮아있어. 치밀한 데이터 분류, 정교한 공정 제어 등은 선조들이 이미 융합적 사고를 통해 최상의 결과물을 만들어냈음을 보여주는 명백한 사실이지.")
        elif view == "비판적 관점":
            st.write(f"**Q: 당신을 만들기 위해 치렀던 사회적 비용이나 희생에 대해 어떻게 생각하나요?**")
            st.write(f"**A:** 나는 국가적 사업이었기에 많은 백성의 노역이 필요했어. 하지만 그것이 소수의 권력을 위한 것이었는지, 아니면 나처럼 {user_interest}의 보급을 통해 만백성을 이롭게 하려 한 것이었는지를 비판적으로 구별해보는 것이 너의 공부에 큰 도움이 될 거야.")
        else:
            st.write(f"**Q: 동시대 다른 나라의 유산과 비교했을 때 당신만의 독보적 가치는?**")
            st.write(f"**A:** 다른 나라에도 비슷한 기록물이나 도구가 있지만, 나처럼 정교한 제작 방식과 보존 상태를 유지하는 경우는 드물어. 이것이 바로 우리 민족이 가진 뛰어난 기록 문화와 기술력의 증거란다.")

        # 탐방 기획안
        st.write("---")
        st.subheader("🗺️ 테마 탐방 기획안")
        st.success(f"**- 제목:** {user_interest} 전문가의 눈으로 본 '{data['title']}' 다시보기")
        st.write(f"**- 필수 관람 포인트:** 유산의 겉모습이 아니라, 그것이 만들어진 '공정'과 '목적'에 집중하세요. 특히 {user_interest}적 관점에서 유산이 현대 사회에 주는 메시지를 메모하며 관람하는 것이 핵심입니다.")
