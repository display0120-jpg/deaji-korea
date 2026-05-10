import streamlit as st
import requests

# 위키백과에서 정보를 가져오는 함수 (인증키 필요 없음!)
def get_wiki_data(q):
    url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{q.replace(' ', '_')}"
    headers = {'User-Agent': 'HeritageProject/1.0'}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        return None

# --- 웹사이트 레이아웃 ---
st.set_page_config(page_title="수행평가 헬퍼", page_icon="📜")

st.title("🏛️ 문화유산 탐구 인터뷰 생성기")
st.write("문화재 이름을 입력하면 수행평가 양식에 맞춰 내용을 정리해 드립니다.")

# 검색창
target = st.text_input("문화유산 이름을 입력하세요 (예: 석굴암, 경복궁, 고인돌)", "석굴암")

if st.button("수행평가 자료 생성"):
    data = get_wiki_data(target)
    
    if data:
        # 기본 정보 전시
        st.success(f"### [선정한 문화유산: {data['title']}]")
        if 'thumbnail' in data:
            st.image(data['thumbnail']['source'], width=400)
        
        content = data['extract'] # 위키백과 요약 내용
        
        # 수행평가 양식에 따른 자동 구성
        st.divider()
        
        # 1. 특징 및 사상
        st.subheader("🎤 인터뷰 1 (특징 및 사상)")
        st.info(f"**Q: {data['title']}이 만들어진 당시 사람들의 생각은 어떠했나요?**")
        st.write(f"**A:** {data['title']}은 당시의 시대적 배경과 정신을 잘 보여줍니다. 기록에 따르면 {content[:150]}... 와 같은 특징이 있어 당시 사람들에게 매우 중요한 상징이었습니다.")

        # 2. 역사적 시련 및 변화
        st.subheader("🎤 인터뷰 2 (역사적 시련 및 변화)")
        st.info(f"**Q: 세월을 거치며 겪었던 시련이나 변화가 있었나요?**")
        st.write(f"**A:** 오랜 세월 동안 자연적인 노후화나 전쟁 등을 겪기도 했지만, 현재는 그 가치를 인정받아 국가적인 보호를 받고 있습니다. {data['title']}의 보존 상태는 우리가 역사를 기억하는 중요한 연결고리가 됩니다.")

        # 3. 비판적/융합적 관점 (과학적 원리)
        st.subheader("🎤 인터뷰 3 (융합적 관점 - 과학/예술)")
        st.info(f"**Q: 이 유산에 담긴 특별한 원리는 무엇인가요?**")
        st.write(f"**A:** 건축학적 혹은 예술적으로 보았을 때, 매우 정교한 기술이 적용되었습니다. 당시의 기술력으로 이러한 구조를 완성했다는 점은 오늘날의 시각에서도 매우 놀라운 '융합적 성과'라고 볼 수 있습니다.")

        # 4. 탐방 기획안 예시
        st.divider()
        st.subheader("📍 테마 탐방 기획안 초안")
        st.write(f"**기획 제목:** [역사 속으로] {data['title']}에 담긴 조상들의 숨결 찾기")
        st.write(f"**관람 포인트:** 위키백과 설명에서 강조된 부분을 중심으로, 실제 현장에서 그 웅장함과 세밀한 조각(또는 구조)을 직접 확인하는 것이 중요합니다.")

    else:
        st.error("정보를 찾을 수 없습니다. 문화재 이름을 정확히 입력해 주세요!")

st.sidebar.write("### 💡 작성 팁")
st.sidebar.info("이 사이트는 위키백과 데이터를 기반으로 뼈대를 잡아줍니다. 실제 제출 시에는 학교 선생님이 나눠주신 안내문의 '비판적 관점' 등을 본인의 생각으로 조금 더 채워 넣으세요!")
