import streamlit as st
import pandas as pd
from google import genai
import gspread
from google.oauth2.service_account import Credentials
import datetime
import time

# 1. 페이지 기본 설정 및 타이틀
st.set_page_config(page_title="AI 면담일지 시스템 2.0", layout="wide")

# 🌟 프리미엄 커스텀 CSS 테마 (사이드바 제거 버전)
st.markdown("""
<style>
[data-testid="stHeader"] { visibility: hidden; height: 0%; }
div.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
.stApp { background-color: #f8f9fa !important; }
.sb-spot-tag { font-size: 14px; font-weight: bold; color: #2563eb; background-color: #eff6ff; padding: 6px 14px; border-radius: 20px; display: inline-block; margin-bottom: 10px; }
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
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 🛠️ [환경설정] 매니저님의 복사 키 이식 구역
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

SPOT_CONFIG = {
    "사내카페 (kafe5)": {
        "spreadsheet_id": "1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "kafe5",
        "employees": ["루크", "앤버", "아이사"]
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
        raw_data = worksheet.get("A9:F1000")
        if not raw_data:
            return worksheet, pd.DataFrame()
        headers = [str(h).strip() for h in raw_data[0]]
        rows = raw_data[1:]
        if not rows:
            df = pd.DataFrame(columns=headers)
            return worksheet, df
        padded_rows = []
        for r in rows:
            if len(r) < len(headers):
                r = r + [""] * (len(headers) - len(r))
            padded_rows.append(r[:len(headers)])
        df = pd.DataFrame(padded_rows, columns=headers)
        return worksheet, df
    except Exception as e:
        st.error(f"시트 데이터를 읽어오는 중 오류가 발생했습니다: {e}")
        return None, pd.DataFrame()

# 💡 [구조 혁신] 숨어버리는 사이드바를 없애고 메인 상단 화면에 크루 선택창을 시원하게 배치합니다!
st.markdown(f'<div class="sb-spot-tag">🏢 현재 선택된 스팟: {current_spot}</div>', unsafe_allow_html=True)

col_sel1, col_sel2 = st.columns([2, 5])
with col_sel1:
    selected_user = st.selectbox("👤 대시보드를 조회할 크루 선택:", spot_info["employees"])
with col_sel2:
    st.write("") # 간격 맞춤용
    st.write("") 
    if st.button("🚪 시스템 로그아웃", key="logout_btn"):
        st.session_state["logged_in_spot"] = None
        st.rerun()

st.markdown("<hr style='margin-top:10px; margin-bottom:20px; border-top:2px solid #2563eb;'>", unsafe_allow_html=True)

worksheet_obj, final_df = load_sheet_data(spot_info["spreadsheet_id"], selected_user)
total_meetings = len(final_df) if not final_df.empty else 0

st.markdown(f"""
<div class='crew-top-card'>
    <div style='display: flex; align-items: center;'>
        <div class='crew-avatar'>{selected_user[0]}</div>
        <div class='crew-meta'>
            <p class='crew-name'>{selected_user} 크루</p>
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

col1, col2, col3, _ = st.columns([1.5, 1.5, 1.5, 4.5])
with col1:
    if st.button("📝 실시간 면담 피드", use_container_width=True): st.session_state["active_tab"] = "면담일지"
with col2:
    if st.button("🤖 AI 카테고리 브리핑", use_container_width=True): st.session_state["active_tab"] = "AI분석"
with col3:
    if st.button("➕ 새 면담 즉시 입력", use_container_width=True): st.session_state["active_tab"] = "면담입력"

st.markdown("<hr style='margin-top:10px; margin-bottom:25px; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

# 1️⃣ [면담일지 피드] 탭 영역 (image_dbfea0 프리미엄 카드 레이아웃 완벽 고정)
if st.session_state["active_tab"] == "면담일지":
    st.markdown('<h3>📋 실시간 면담 일지 피드</h3>', unsafe_allow_html=True)
    if final_df.empty:
        st.info("현재 등록된 면담 일지 데이터가 없습니다. 첫 기록을 등록해 보세요!")
    else:
        category_filter = st.selectbox("정렬 카테고리 필터", ["전체 구분"] + list(final_df['구분'].dropna().unique()), key="feed_filter_box")
        filtered_df = final_df.copy()
        if category_filter != "전체 구분":
            filtered_df = filtered_df[filtered_df['구분'] == category_filter]
        
        latest_df = filtered_df.tail(5).iloc[::-1]
        for idx, row in latest_df.iterrows():
            date_val = row.get('일자', '')
            type_val = row.get('구분', '')
            subtype_val = row.get('세부 구분', '')
            content_val = str(row.get('내용', '')).replace('\n', '<br>')
            author_val = row.get('면담자/작성자', row.get('면담자', '명시되지 않음'))
            
            st.markdown(f"""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 16px; border-left: 5px solid #2563eb;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="font-weight: bold; color: #1e3a8a; margin-right: 8px; font-size: 15px;">📅 {date_val}</span>
                        <span style="background-color: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 4px;">{type_val}</span>
                        <span style="background-color: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{subtype_val}</span>
                    </div>
                    <div style="font-size: 13px; color: #64748b;">작성자: <b>{author_val}</b></div>
                </div>
                <div style="font-size: 14.5px; color: #334155; line-height: 1.6; padding: 2px 5px;">
                    {content_val}
                </div>
            </div>
            """, unsafe_allow_html=True)

# 2️⃣ [AI분석] 탭 영역 (초기 버전 스마트 카테고리 자동화 완벽 작동형)
elif st.session_state["active_tab"] == "AI분석":
    st.markdown("<h3>🤖 Gemini AI 카테고리별 실시간 종합 브리핑</h3>", unsafe_allow_html=True)
    if final_df.empty:
        st.info("분석할 면담 히스토리 데이터가 없습니다.")
    else:
        with st.spinner("구글 고성능 제미나이 AI가 카테고리별로 데이터를 종단 스크리닝 중..."):
            categories = ["월 면담", "근무 리뷰", "위생", "근태 관리"]
            combined_context = ""
            for cat in categories:
                cat_df = final_df[final_df['구분'] == cat]
                if not cat_df.empty:
                    combined_context += f"■ [{cat}] 카테고리 데이터 (최근 기록순):\n"
                    for _, row in cat_df.tail(10).iterrows():
                        combined_context += f"- 일자: {row.get('일자','')}, 내용: {row.get('내용','')}\n"
                    combined_context += "\n"
            etc_df = final_df[~final_df['구분'].isin(categories)]
            if not etc_df.empty:
                combined_context += "■ [기타 사항] 카테고리 데이터:\n"
                for _, row in etc_df.tail(5).iterrows():
                    combined_context += f"- 일자: {row.get('일자','')}, 내용: {row.get('내용','')}\n"
            
            prompt = f"""당신은 장애인 표준사업장 최고 전문 지도원입니다. 
            제공된 크루의 면담 데이터를 바탕으로, 반드시 아래 명시된 카테고리별로 구역을 나누어 가이드라인 리포트를 작성하세요.
            이때 이모지(emoji)를 적절히 활용하여 매니저가 한눈에 읽기 쉽게 가독성을 극대화하세요.

            [분석 요청 카테고리]
            1. 📅 월 정기 면담 종합 요약
            2. ☕ 현장 근무 리뷰 및 직무 수행 평가
            3. ✨ 개인 위생 및 복장 규정 준수 상태
            4. ⏰ 근태 관리 및 돌발 이슈 리스크 진단

            데이터 내용:\n{combined_context}"""
            
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-top: 6px solid #10b981; line-height: 1.8;">
                    {response.text}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"AI 통신 에러가 발생했습니다: {e}")

# 3️⃣ [면담입력] 탭 영역
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
