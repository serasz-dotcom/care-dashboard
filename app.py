import streamlit as st
import pandas as pd
from google import genai
import time

# 1. 페이지 기본 설정 및 타이틀 (반드시 가장 첫 줄에 위치)
st.set_page_config(page_title="AI 면담일지 대시보드", layout="wide")

# 🌟 [디자인 최종 완성] 마우스 호버(Hover) 시 빨간색 오타 테마를 파란색으로 전면 교체한 CSS
st.markdown("""
<style>
/* Streamlit 기본 고정 헤더 영역을 숨겨 상단 잘림 현상 완벽 방지 */
[data-testid="stHeader"] {
    visibility: hidden;
    height: 0%;
}
div.block-container { 
    padding-top: 2rem !important; 
    padding-bottom: 2rem !important; 
}

/* 상단 메인 타이틀 선명한 파란색 강제 고정 */
.blue-main-title {
    color: #2563eb !important;
    font-weight: 800 !important;
    font-size: 28px !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 흰색 본문 카드 박스 디자인 슬림화 */
div[data-testid="stVerticalBlock"] > div[border="true"] {
    background-color: var(--background-color) !important;
    border: 1px solid var(--text-color) !important;
    border-radius: 16px !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02) !important;
    margin-bottom: 12px !important;
}

/* 안과 앱 시안 스타일: 커스텀 알약 버튼 마스터 레이아웃 구조 */
div[data-testid="stPills"] div[role="listbox"] {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important;
    gap: 10px !important;
    width: 100% !important;
}

/* 기본 알약 단추 스타일 */
div[data-testid="stPills"] button {
    width: 100% !important;
    height: 54px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    background-color: var(--background-color) !important;
    border: 1px solid var(--text-color) !important;
    color: var(--text-color) !important;
    margin: 0 !important;
    transition: all 0.15s ease-in-out !important;
}

/* 🌟 [요청 반영] 마우스를 올렸을 때(Hover)나 포커스가 갔을 때 파란색으로 변경 */
div[data-testid="stPills"] button:hover, 
div[data-testid="stPills"] button:focus, 
div[data-testid="stPills"] button:active {
    border-color: #2563eb !important;
    color: #2563eb !important;
    background-color: rgba(37, 99, 235, 0.04) !important;
}

/* 🔷 클릭해서 완전히 선택되었을 때 안과 앱 블루(#2563EB) 배경 고정 스타일 */
div[data-testid="stPills"] button[aria-selected="true"] {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
}
div[data-testid="stPills"] button[aria-selected="true"]:hover,
div[data-testid="stPills"] button[aria-selected="true"]:focus {
    background-color: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

/* 📱 상단 모바일 스타일 블루 웰컴 배너 구역 */
.mobile-top-banner {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    border-radius: 20px;
    padding: 26px;
    margin-bottom: 18px;
    box-shadow: 0 10px 20px rgba(37, 99, 235, 0.15);
}
.mobile-title { font-size: 22px !important; font-weight: 800; margin-bottom: 4px; color: #ffffff !important; }
.mobile-subtitle { font-size: 13.5px !important; color: #93c5fd !important; font-weight: 500; }

/* 배너 내부 프로필 카드 박스 */
.profile-card {
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 14px;
    padding: 16px;
    margin-top: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.profile-name { font-size: 18px !important; font-weight: 700; color: #1e293b !important; }
.profile-desc { font-size: 12.5px !important; color: #64748b !important; margin-top: 1px; }

/* OPD 세로 리포트 카드 디자인 컴포넌트 */
.opd-card {
    padding: 22px; border-radius: 16px; margin-bottom: 16px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.02);
    border-left: 6px solid #64748b; background-color: var(--background-color);
    color: var(--text-color);
}
.opd-strong { border-left-color: #2563eb; background-color: rgba(37, 99, 235, 0.05); }
.opd-warning { border-left-color: #f59e0b; background-color: rgba(245, 158, 11, 0.05); }
.opd-success { border-left-color: #10b981; background-color: rgba(16, 185, 129, 0.05); }
.opd-danger  { border-left-color: #ef4444; background-color: rgba(239, 68, 68, 0.05); }

.opd-title { font-size: 16.5px !important; font-weight: bold; margin-bottom: 8px; }
.opd-content { font-size: 14px !important; line-height: 1.6 !important; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 구글 시트 주소와 API 키 설정 구역
# =========================================================================
SPOT_CONFIG = {
    "사내카페 (kafe5)": {
        "base_url": "https://docs.google.com/spreadsheets/d/1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "kafe5",
        "employees": {
            "루크(장종원)": "1518673498",
            "휴버트(강채운)": "1231497521"
        }
    }
}
GEMINI_API_KEY = "AQ.Ab8RN6LHyW0ZveQOsrc_6nGFB9tSqA71glqGaH4NxDP311UdRA"
# =========================================================================

# --- 세션 검사 및 초기화 ---
if "logged_in_spot" not in st.session_state: st.session_state["logged_in_spot"] = None
if "ai_report_data" not in st.session_state: st.session_state["ai_report_data"] = {}

# 로그인 창 구현
if st.session_state["logged_in_spot"] is None:
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🔒 사내 면담 관리 시스템 권한 인증</h2>", unsafe_allow_html=True)
    left_co, cent_co, last_co = st.columns([1, 1.8, 1])
    with cent_co:
        with st.container(border=True):
            selected_spot = st.selectbox("접근할 근무 스팟 선택:", list(SPOT_CONFIG.keys()))
            input_password = st.text_input(f"🔑 [{selected_spot}] 전용 비밀번호:", type="password")
            st.write("")
            if st.button("🚀 대시보드 진입", use_container_width=True):
                if input_password == SPOT_CONFIG[selected_spot]["password"]:
                    st.session_state["logged_in_spot"] = selected_spot
                    st.success("🔓 인증 성공!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()

# --- 메인 시스템 단계 ---
current_spot = st.session_state["logged_in_spot"]
spot_data = SPOT_CONFIG[current_spot]

# 상단 타이틀 행 정렬
col_title, col_logout = st.columns([7.8, 2.2])
with col_title:
    st.markdown('<p class="blue-main-title">🤝 AI 면담일지 대시보드</p>', unsafe_allow_html=True)
with col_logout:
    if st.button("🚪 시스템 로그아웃", use_container_width=True):
        st.session_state["logged_in_spot"] = None
        st.session_state["ai_report_data"] = {}
        st.rerun()

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# 사이드바 세팅
st.sidebar.markdown(f"### 👤 소속 크루 프로필 조회")
employee_list = list(spot_data["employees"].keys())
selected_user = st.sidebar.selectbox("대상 크루를 선택하세요:", employee_list)
st.sidebar.markdown("---")
st.sidebar.caption(f"현재 선택된 스팟: **{current_spot}**")

# 구글 데이터 내보내기 주소 변환
raw_url = spot_data["base_url"].strip()
clean_url = raw_url.split("/edit")[0] if "/edit" in raw_url else raw_url.split("/export")[0] if "/export" in raw_url else raw_url
selected_gid = spot_data["employees"][selected_user]
current_sheet_url = f"{clean_url}/export?format=csv&gid={selected_gid}"

@st.cache_data(ttl=3)
def load_data(url):
    try:
        df = pd.read_csv(url, skiprows=8)
        df.columns = df.columns.str.strip()
        if '내용' not in df.columns or df.empty:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            
        valid_cols = ['일자', '구분', '세부 구분', '내용', '면담자/작성자', '누적 횟수', '누적회수']
        existing_cols = [c for c in df.columns if c in valid_cols]
        if existing_cols:
            df = df[existing_cols]
            
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace('nan', '').str.strip()
        return df
    except: 
        return None

final_df = load_data(current_sheet_url)
if final_df is None or final_df.empty:
    final_df = pd.DataFrame(columns=['일자', '구분', '세부 구분', '내용', '면담자/작성자', '누적 횟수'])

# 📱 1단계: 모바일 UI 스타일 최상단 블루 배너
st.markdown(f"""
<div class='mobile-top-banner'>
    <div class='mobile-title'>안녕하세요, 관리자님 👋</div>
    <div class='mobile-subtitle'>{current_spot} 현장 크루들의 케어 상태를 실시간 체크 중입니다.</div>
    <div class='profile-card'>
        <div>
            <div class='profile-name'>👤 {selected_user} 크루</div>
            <div class='profile-desc'>실시간 구글 면담일지 분석 대기 중</div>
        </div>
        <div style='font-size:12px; font-weight:bold; color:#2563eb; background-color:#eff6ff; padding:6px 12px; border-radius:30px;'>정상 근무 중</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 💡 2단계 & 3단계 통합: 10대 메뉴 마스터 가동
with st.container(border=True):
    st.markdown("<p style='color:#2563eb; font-weight:700; margin-bottom:12px; font-size:15px;'>📱 AI 케어 포털 - 마이메뉴 일지 탐색</p>", unsafe_allow_html=True)
    
    action_type = st.pills(
        label="탐색할 카테고리를 터치하세요:",
        options=[
            "📋 종합 OPD 분석", 
            "📍 근무지 이동", 
            "⏰ 근태 관리", 
            "📅 월면담", 
            "📊 근무 리뷰", 
            "📊 업무 발전", 
            "🧼 개인 위생", 
            "☕ 매뉴얼 준수", 
            "🤝 직장 예절", 
            "🔍 기타 사항"
        ],
        label_visibility="collapsed"
    )

# 결과 출력 핸들링 구역
if action_type:
    if action_type == "📋 종합 OPD 분석":
        category_kor_name = "OPD 종합 보고서"
        display_df = final_df.copy()
    else:
        if action_type == "📍 근무지 이동": search_keyword = "이동|배치|스팟|전환|근무지|파견"; category_kor_name = "근무지 이동"
        elif action_type == "⏰ 근태 관리": search_keyword = "근태|지각|결근|조퇴|무단|휴가|병가"; category_kor_name = "근태 관리"
        elif action_type == "📅 월면담": search_keyword = "면담|월면담|정기|상담"; category_kor_name = "월면담"
        elif action_type == "📊 근무 리뷰": search_keyword = "리뷰|평가|근무|태도|중간|점검"; category_kor_name = "근무 리뷰"
        elif action_type == "📊 업무 발전": search_keyword = "발전|향상|성장|습득|성취|도전|개선"; category_kor_name = "업무 발전"
        elif action_type == "🧼 개인 위생": search_keyword = "위생|청결|마스크|손 씻기|복장|샤워|단정|양치"; category_kor_name = "개인 위생"
        elif action_type == "☕ 매뉴얼 준수": search_keyword = "매뉴얼|준수|미준수|제조|순서|레시피|수칙|실수"; category_kor_name = "매뉴얼 준수"
        elif action_type == "🤝 직장 예절": search_keyword = "예절|태도|인사|소통|동료|존중|갈등|경어|존댓말"; category_kor_name = "직장 예절"
        elif action_type == "🔍 기타 사항": search_keyword = "기타|특이|사항|기록|종합"; category_kor_name = "기타 사항"

        if not final_df.empty and '내용' in final_df.columns:
            display_df = final_df[final_df['내용'].str.contains(search_keyword, na=False, case=False) | final_df['구분'].str.contains(search_keyword, na=False, case=False)]
        else: 
            display_df = pd.DataFrame()

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container(border=True):
        if action_type != "📋 종합 OPD 분석":
            st.markdown(f"<h5>📋 [{category_kor_name}] 관련 현장 일지 리스트</h5>", unsafe_allow_html=True)
            st.dataframe(display_df, use_container_width=True)

        cache_key = f"{selected_user}_{action_type}"
        if "last_cache_key" not in st.session_state or st.session_state["last_cache_key"] != cache_key:
            st.session_state["last_cache_key"] = cache_key
            st.session_state["ai_report_data"] = {}

        if not st.session_state["ai_report_data"]:
            with st.spinner("Gemini AI 실시간 빅데이터 인사이트 스크리닝 중..."):
                context = ""
                if not display_df.empty:
                    for idx, row in display_df.tail(40).iterrows():
                        context += f"[{row.get('일자','')}] 구분: {row.get('구분','')}, 내용: {row.get('내용','')}\n"
                else:
                    context = "현재 등록된 관련 면담 기록이 없습니다."

                if action_type == "📋 종합 OPD 분석":
                    final_prompt = f"""당신은 장애인 표준사업장의 최고 전문 지도원입니다. 다음 데이터를 깊이 분석해 OPD 가이드를 작성하세요.
                    [PART1], [PART2], [PART3], [PART4] 구분 부호를 반드시 포함하고 마크다운 글머리기호(•)를 사용하세요.
                    [PART1] 강점
                    [PART2] 중요하게 여길 것 (건강과 안전)
                    [PART3] 중요하게 여길 것 (좋아하는 것, 소중한 것)
                    [PART4] 잘 지원해줄 수 있는 방법 (주의사항, 장애 특성, 기질적 측면, 싫어하는 부분)
                    데이터: {context}"""
                else:
                    final_prompt = f"""당신은 장애인 표준사업장 지도원입니다. 4개 구문으로 나누어 작성하세요. [PART1], [PART2], [PART3], [PART4] 부호를 포함하세요.
                    [PART1] 요약 상태 [PART2] 보완 및 누락점 [PART3] 교육 지원 방향 [PART4] 칭찬 및 격려 팁
                    데이터: {context}"""

                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=final_prompt)
                    raw_text = response.text
                    parts = {"p1": "기록이 부족합니다.", "p2": "기록이 부족합니다.", "p3": "기록이 부족합니다.", "p4": "기록이 부족합니다."}
                    if "[PART1]" in raw_text and "[PART2]" in raw_text and "[PART3]" in raw_text and "[PART4]" in raw_text:
                        parts["p1"] = raw_text.split("[PART1]")[1].split("[PART2]")[0].strip()
                        parts["p2"] = raw_text.split("[PART2]")[1].split("[PART3]")[0].strip()
                        parts["p3"] = raw_text.split("[PART3]")[1].split("[PART4]")[0].strip()
                        parts["p4"] = raw_text.split("[PART4]")[1].strip()
                    else: 
                        parts["p1"] = raw_text
                    parts["context_data"] = context
                    st.session_state["ai_report_data"] = parts
                except Exception as e: 
                    st.error(f"구글 AI 통신 실패: {e}")

        if st.session_state["ai_report_data"]:
            report = st.session_state["ai_report_data"]

            if action_type == "📋 종합 OPD 분석":
                st.markdown(f"<h3 style='margin-bottom:20px; font-weight:700;'>📋 {selected_user} 크루 마스터 One-Page Profile</h3>", unsafe_allow_html=True)
                st.markdown(f"<div class='opd-card opd-strong'><div class='opd-title'>💪 1. {selected_user} 크루의 강점</div><div class='opd-content'>{report.get('p1','').replace('\n', '<br>')}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='opd-card opd-warning'><div class='opd-title'>⚠️ 2. {selected_user}를 위해 중요한 것 (건강과 안전)</div><div class='opd-content'>{report.get('p2','').replace('\n', '<br>')}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='opd-card opd-success'><div class='opd-title'>❤️ 3. {selected_user}에게 중요한 것 (좋아하는 것, 소중한 것)</div><div class='opd-content'>{report.get('p3','').replace('\n', '<br>')}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='opd-card opd-danger'><div class='opd-title'>💡 4. {selected_user}를 잘 지원해줄 수 있는 방법 (주의사항, 특성)</div><div class='opd-content'>{report.get('p4','').replace('\n', '<br>')}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown("<h5 style='margin-bottom:15px;'>🎯 핵심 맞춤형 AI 인사이트 탐색</h5>", unsafe_allow_html=True)
                
                # 하단 인사이트 4대 단추 선택 뷰
                view_type = st.pills(
                    label="세부 분석 데이터 고르기:",
                    options=["📋 1. 상태 요약본 보기", "❌ 2. 누락/보완점 보기", "💡 3. 맞춤 지원/교육 방향", "👏 4. 칭찬 및 격려 행동 팁"],
                    default="📋 1. 상태 요약본 보기",
                    label_visibility="collapsed"
                )

                view_key = "p1" if "1. 상태 요약본" in view_type else "p2" if "2. 누락/보완점" in view_type else "p3" if "3. 맞춤 지원" in view_type else "p4"
                st.markdown(f"<p style='font-size:14px; font-weight:bold; color:#2563eb; margin-top:15px;'>🤖 Gemini AI 결과 -> {view_type}</p>", unsafe_allow_html=True)
                st.info(report.get(view_key, "내용을 불러올 수 없습니다."))

            # 5번 질문 가이드 박스 마감
            st.markdown("<br><hr style='border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown(f"### 🔍 제미나이 마스터에게 추가 질문하기")
            user_question = st.text_input(f"❓ [{selected_user}] 크루에 대해 더 알고 싶은 사항:", placeholder="예: 이 크루가 돌발 상황을 마주했을 때 제지하는 효과적인 대화법이 있나요?")
            if st.button("💬 심층 분석 질문 답변 받기"):
                if user_question.strip() != "":
                    with st.spinner("제미나이 AI 히스토리 대조 가이드라인 작성 중..."):
                        try:
                            client = genai.Client(api_key=GEMINI_API_KEY)
                            c_response = client.models.generate_content(model='gemini-2.5-flash', contents=f"장애인 표준사업장 지도원으로서 답변하세요.\n질문: {user_question}\n데이터: {report.get('context_data','')}")
                            st.success("💡 답변 결과")
                            st.write(c_response.text)
                        except Exception as e: 
                            st.error(f"오류: {e}")
