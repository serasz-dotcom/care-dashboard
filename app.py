import streamlit as st
import pandas as pd
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import time

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(page_title="AI 면담일지 시스템 2.0", layout="wide")

# 🌟 [인앱 UI 완벽 재현] 보내주신 시안 어플리케이션 느낌의 프리미엄 커스텀 CSS 테마
st.markdown("""
<style>
[data-testid="stHeader"] { visibility: hidden; height: 0%; }
div.block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; }
.stApp { background-color: #f8f9fa !important; }
.sb-header { font-size: 18px !important; font-weight: 700; color: #1e293b; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
.sb-spot-tag { font-size: 12px; font-weight: bold; color: #2563eb; background-color: #eff6ff; padding: 4px 10px; border-radius: 20px; margin-bottom: 15px; display: inline-block; }
.crew-top-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.01); }
.crew-avatar { width: 52px; height: 52px; background-color: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #2563eb; font-size: 18px; border: 2px solid #e2e8f0; }
.crew-meta { margin-left: 14px; flex-grow: 1; }
.crew-name { font-size: 22px !important; font-weight: 800; color: #1e293b; margin: 0; }
.crew-sub { font-size: 13px !important; color: #64748b; margin-top: 2px; }
.status-badge { font-size: 12px; font-weight: bold; color: #16a34a; background-color: #f0fdf4; padding: 6px 12px; border-radius: 30px; }
.indicator-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
.ind-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.01); }
.ind-label { font-size: 13px !important; color: #64748b; font-weight: 600; display: flex; align-items: center; gap: 5px; }
.ind-value { font-size: 26px !important; font-weight: 800; margin-top: 6px; margin-bottom: 8px; }
.ind-value.normal { color: #f59e0b; }
.ind-value.good { color: #16a34a; }
.ind-value.growth { color: #2563eb; }
.ind-sub { font-size: 12px !important; color: #94a3b8; }
.ind-bar { height: 5px; border-radius: 10px; margin-top: 4px; }
.log-feed-card { background-color: #ffffff; border-bottom: 1px solid #f1f5f9; padding: 20px 5px; }
.log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.log-date { font-size: 14px; font-weight: 700; color: #64748b; }
.log-tag { font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 6px; }
.log-tag.review { color: #2563eb; background-color: #eff6ff; }
.log-tag.interview { color: #16a34a; background-color: #f0fdf4; }
.log-tag.hygiene { color: #06b6d4; background-color: #ecfeff; }
.log-author { font-size: 13px; color: #94a3b8; }
.log-body { font-size: 14.5px !important; color: #334155; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 🛠️ [환경설정] 매니저님의 발급 데이터 입력 구역
# =========================================================================
GEMINI_API_KEY = "c1d5423b657ff8d3f312e557962be880da2ffd71"

# 구글 서비스 계정 JSON 키 데이터 바인딩
CREDENTIALS_DICT = {
    "type": "service_account",
    "project_id": "maximal-ceiling-500606-m5",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDUhuXLpPQxKWOp\nWdpsWyJdBQU4pM2yFIEcPAOq2q+aE10c7auwWXZFBFeRmAp5Hd13cm5IFbz4T+KC\nruhyrE+zsEdCqCU/NzoGmZJMoP3QGreR8CxN337ZJ2/k9Mj8HIlesay5OnesSfFw\nDdJ2+5fCtkl8HfPVN7lOfZJVwd7DESGBUfml3VTYhLlXsj6fU276V9sBpbeXxyb9\n42Yvz2moi9SlJF9lMbdkvUefHemYe29T7Jjony8VIAElC0bwAYe7xvmAS9ply12s\n+Z5n/OQIKC4Qje7pWHJcFN+mCLT3z1dqS7dD15AqDhuKlPovAyCSSSpxQzPwBt8H\n9U83HkIBAgMBAAECggEAA6vkQA00oL11I3b8vyl14a3VW2ymwbWj+K+6un1g/OQ/\nvrZbucYEioha1kDjpsL9e/ObSciCWrclPm+0w/e2asVtUw6iPMIrUPOJ46QBA9LV\nAALqU7ARj2vPKDaTBZ6dQD2z3QFQZvFiEoxSlKFKYQqSy2pIYj2+XZztZb4zJyMr\nu0NtQCXmkI1J/SfxfZj/+FLn4cpuM6Rsmq3uaotPvqZDfsfYJ+eP5LwLnumROxmp\nrtHviMdG5E1DOzSBq00rXQLv/4gQLqWQEvE/sd1wcglu59a4qsrHlEO/jfetL3vX\nrTnoNZx4w2OX5HZuNd+ulq/TxZvjSCNna0TpY8KRoQKBgQDrqyLbyrg9Bec2e7io\nevayTRXC4m1862NzZ7/Kof9lXy8wJVooEkPkdWNZDDFT7mJXMiCK4uAxG91Z5oAL\nsTJpQGjhqdOzSQMdu6k2jh8eCEsKZuaONDa7qaS/GxGBJm91GBXnsCx8kE/1POKs\n4SbABHZQEJqAGvUP5Uf4qeP9mQKBgQDm3Kr8o0xGo6dzdUvb9vP0feChN2GI2ucr\nXcpr2WWGzS9jB2HXNNgWU1h+sbVq91ci86SOJMQ6x+UIvrKHTRdADonE0qYxuuT0\nRK11bg3w7db4ykLUoE2vOaf7Em6E2Ani6JhzBChCeb4CtyTT7LF/yZzIfcEI2H6i\nBiZGFPGYqQKBgQDFOV1cz1RMTWpoIDYzWWSnZvd1NwUl6+A4rnTFYblY3sWg50GC\nE3cZ9FuGJDwL344RJvQxBxlUP9uI5uv13P8xMiQT5ooymkGvWmOMMng8K/iQ5fjA\nvVWoy5oCDOcjTEUum0+Jq9gvDp67v45725kQTSuuaZbC6sx31wvaQGN60QKBgFlG\nFfzyLOnYGUXlovshqT7venD9WIMym1hCwaco/0C8kcmKrkQpVDJ18m+zysLdeN20\nN/sbrqJIcIIMND9sCUSlGpN5Hfl3G1h2Qll5wHxdjNbSaDuO7duHwTSu8PwACvqr\nFWDMx8DFETw9lEk7a3xN+4nwTzhbd8Sx+hT5vl9ZAoGBAIMnDRuZhNJX4widaIrt\nU4tWxLg8GpsHjXObKmo+EaNZJ9UzqGDXMHFiN10Bw+BcRDkdjRFFl2Q8t4aA1Dlu\nTzkDb+ge8pgNLeiGLq+D+K9kAmNsUV9MrlRoQYPn4WvWVMfBu4vt5lOb+9v8ocbi\nNRyBZ3CO/JXGwApzDM2RD1CA\n-----END PRIVATE KEY-----\n",
    "client_email": "care-manager@maximal-ceiling-500606-m5.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token"
}

# 스팟별 구글 시트 고유 ID 세팅
SPOT_CONFIG = {
    "사내카페 (kafe5)": {
        "spreadsheet_id": "1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "kafe5",
        "employees": ["루크", "휴버트"]
    },
    "행정지원스팟 (office7)": {
        "spreadsheet_id": "여기에_행정지원_시트_ID_입력", 
        "password": "office7",
        "employees": ["민준", "지수", "하람"]
    }
}
# =========================================================================

if "logged_in_spot" not in st.session_state: st.session_state["logged_in_spot"] = None
if "active_tab" not in st.session_state: st.session_state["active_tab"] = "면담일지"

if st.session_state["logged_in_spot"] is None:
    st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 사내 면담일지 시스템 권한 인증</h2>", unsafe_allow_html=True)
    _, cent_co, _ = st.columns([1, 1.5, 1])
    with cent_co:
        with st.container(border=True):
            selected_spot = st.selectbox("접근할 근무 스팟 선택:", list(SPOT_CONFIG.keys()))
            input_password = st.text_input(f"🔑 [{selected_spot}] 비밀번호:", type="password")
            if st.button("🚀 시스템 로그인", use_container_width=True):
                if input_password == SPOT_CONFIG[selected_spot]["password"]:
                    st.session_state["logged_in_spot"] = selected_spot
                    st.success("🔓 인증 성공!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()

current_spot = st.session_state["logged_in_spot"]
spot_info = SPOT_CONFIG[current_spot]

@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(CREDENTIALS_DICT, scopes=scope)
    return gspread.authorize(creds)

def load_sheet_data(spreadsheet_id, sheet_name):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        return worksheet, df
    except Exception as e:
        st.error(f"시트 데이터를 읽어오는 중 오류가 발생했습니다: {e}")
        return None, pd.DataFrame()

st.sidebar.markdown('<div class="sb-header">📋 면담일지 시스템</div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<div class="sb-spot-tag">{current_spot}</div>', unsafe_allow_html=True)

search_query = st.sidebar.text_input("🔍 직원 검색...", value="", placeholder="이름 입력...")
filtered_employees = [emp for emp in spot_info["employees"] if search_query.lower() in emp.lower()]

if not filtered_employees:
    st.sidebar.info("검색된 직원이 없습니다.")
    st.stop()

selected_user = st.sidebar.radio("소속 크루 명단", filtered_employees, label_visibility="collapsed")
st.sidebar.markdown("---")
if st.sidebar.button("🚪 시스템 로그아웃", use_container_width=True):
    st.session_state["logged_in_spot"] = None
    st.rerun()

worksheet_obj, final_df = load_sheet_data(spot_info["spreadsheet_id"], selected_user)

total_meetings = len(final_df) if not final_df.empty else 0
st.markdown(f"""
<div class='crew-top-card'>
    <div style='display: flex; align-items: center;'>
        <div class='crew-avatar'>{selected_user[0]}</div>
        <div class='crew-meta'>
            <p class='crew-name'>{selected_user}</p>
            <p class='crew-sub'>{current_spot} · 면담 총 {total_meetings}회 기록됨</p>
        </div>
    </div>
    <div class='status-badge'>정상 근무 중</div>
</div>
""", unsafe_allow_html=True)

anxiety_status = "보통"
hygiene_status = "양호"
growth_status = "성장 중"

if not final_df.empty and '내용' in final_df.columns:
    full_text = " ".join(final_df['내용'].astype(str).tolist())
    if "불안" in full_text or "긴장" in full_text or "이슈" in full_text: anxiety_status = "주의 필요"
    if "위생" in full_text or "복장" in full_text or "미준수" in full_text: hygiene_status = "점검 필요"
    if "성장" in full_text or "칭찬" in full_text or "잘함" in full_text: growth_status = "우수 크루"

st.markdown(f"""
<div class='indicator-container'>
    <div class='ind-card'>
        <div class='ind-label'>😟 불안도</div>
        <div class='ind-value normal'>{anxiety_status}</div>
        <div class='ind-sub'>최근 3개월 평균</div>
        <div class='ind-bar' style='background-color:#f59e0b; width:60%;'></div>
    </div>
    <div class='ind-card'>
        <div class='ind-label'>✨ 위생 상태</div>
        <div class='ind-value good'>{hygiene_status}</div>
        <div class='ind-sub'>최근 3개월 평균</div>
        <div class='ind-bar' style='background-color:#16a34a; width:85%;'></div>
    </div>
    <div class='ind-card'>
        <div class='ind-label'>📈 업무 발전도</div>
        <div class='ind-value growth'>{growth_status}</div>
        <div class='ind-sub'>최근 3개월 평균</div>
        <div class='ind-bar' style='background-color:#2563eb; width:75%;'></div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, _ = st.columns([1.2, 1.2, 1.2, 5.4])
with col1:
    if st.button("📝 면담일지 피드", use_container_width=True): st.session_state["active_tab"] = "면담일지"
with col2:
    if st.button("🤖 AI 브리핑", use_container_width=True): st.session_state["active_tab"] = "AI분석"
with col3:
    if st.button("➕ 새 면담 입력", use_container_width=True): st.session_state["active_tab"] = "면담입력"

st.markdown("<hr style='margin-top:10px; margin-bottom:20px; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

if st.session_state["active_tab"] == "면담일지":
    st.subheader("📋 실시간 면담 일지 피드")
    if final_df.empty:
        st.info("현재 등록된 면담 일지 데이터가 없습니다. 첫 기록을 등록해 보세요!")
    else:
        category_filter = st.selectbox("정렬 카테고리 필터", ["전체 구분", "월 면담", "근무 리뷰", "위생", "기타 사항"])
        display_df = final_df.copy()
        if '일자' in display_df.columns:
            display_df = display_df.sort_values(by='일자', ascending=False)
        if category_filter != "전체 구분":
            display_df = display_df[display_df['구분'] == category_filter]
        for _, row in display_df.iterrows():
            tag_class = "review" if "리뷰" in str(row.get('구분','')) else "interview" if "면담" in str(row.get('구분','')) else "hygiene"
            st.markdown(f"""
            <div class='log-feed-card'>
                <div class='log-header'>
                    <div>
                        <span class='log-date'>📅 {row.get('일자','')}</span>
                        <span class='log-tag {tag_class}'>{row.get('구분','기타')}</span>
                        <span style='font-size:12px; color:#64748b; margin-left:8px;'>{row.get('세부 구분','')}</span>
                    </div>
                    <div class='log-author'>작성자: {row.get('면담자/작성자','엘')}</div>
                </div>
                <div class='log-body'>{str(row.get('내용',''))}</div>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state["active_tab"] == "AI분석":
    st.subheader("🤖 Gemini AI 실시간 종합 보고서 브리핑")
    if final_df.empty:
        st.info("분석할 면담 히스토리 데이터가 없습니다.")
    else:
        with st.spinner("구글 고성능 제미나이 AI가 일지를 종단 검색 중..."):
            context = ""
            for _, row in final_df.tail(30).iterrows():
                context += f"[{row.get('일자','')}] 구분: {row.get('구분','')}, 내용: {row.get('내용','')}\n"
            prompt = f"""당신은 장애인 표준사업장 최고 전문 지도원입니다. 다음 면담 히스토리를 요약 분석하여 리포트를 작성하세요.
            [PART1] 강점 요약 [PART2] 불안도 리스크 진단 [PART3] 위생 상태 평가 [PART4] 업무발전도 가이드라인
            데이터:\n{context}"""
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 통신 에러: {e}")

elif st.session_state["active_tab"] == "면담입력":
    st.subheader(f"➕ {selected_user} 크루 현장 면담 즉시 기록")
    with st.form("interview_form", clear_on_submit=True):
        col_d, col_g = st.columns(2)
        with col_d: form_date = st.date_input("날짜 설정", datetime.date.today())
        with col_g: form_cat = st.selectbox("대구분", ["월 면담", "근무 리뷰", "위생", "근태 관리", "기타 사항"])
        col_s, col_w = st.columns(2)
        with col_s: form_sub = st.selectbox("세부 구분", ["정기 면담", "오전 근무 점검", "오후 근무 점검", "돌발 이슈", "일반 관찰 기록"])
        with col_w: form_author = st.text_input("면담자/작성자 이름", value="세라")
        form_content = st.text_area("✍️ 구체적인 현장 관찰 및 면담 내용")
        submit_btn = st.form_submit_button("🚀 구글 스프레드시트에 즉시 저장하기", use_container_width=True)
        if submit_btn:
            if form_content.strip() == "": st.error("❌ 내용을 입력하세요!")
            elif worksheet_obj is None: st.error("❌ 권한 오류")
            else:
                with st.spinner("저장 중..."):
                    try:
                        date_str = form_date.strftime("%y/%m/%d")
                        new_row = [date_str, form_cat, form_sub, form_content, form_author, total_meetings + 1]
                        worksheet_obj.append_row(new_row)
                        st.success("🎉 구글 시트에 저장 완료!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"실패: {e}")
