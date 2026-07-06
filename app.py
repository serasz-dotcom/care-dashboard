import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정 및 스타일 (블루 테마)
st.set_page_config(page_title="케어 매니저 대시보드", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #ffffff; }
    .stButton>button { background-color: #1e3a8a; color: white; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #3b82f6; }
    .sidebar .sidebar-content { background-color: #1e293b; }
    h1, h2, h3 { color: #3b82f6; }
    div.dashed-box { border: 2px dashed #3b82f6; padding: 20px; border-radius: 10px; background-color: #1e293b; }
    </style>
    """, unsafe_allow_html_tags=True)

# 2. 구글 스프레드시트 연동 설정 및 스팟별 비밀번호 개별 설정
SPOT_CONFIG = {
    "사내카페 (kafe5)": {
        "base_url": "https://docs.google.com/spreadsheets/d/1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "kafe5",  # 사내카페 매니저용 비밀번호
        "employees": {
            "루크(장종원)": "1518673498",
            "휴버트(강채운)": "1231497521"
        }
    },
    "행정지원스팟 (office7)": {
        "base_url": "https://docs.google.com/spreadsheets/d/1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "office7",  # 행정지원 매니저용 비밀번호
        "employees": {
            "테스트크루": "0"
        }
    }
}

# 구글 시트 CSV 변환 함수
def get_google_sheet_url(base_url, gid):
    return f"{base_url}/export?format=csv&gid={gid}"

# 데이터 불러오기 함수
@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        # 컬럼명 공백 제거
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 3. 사이드바 로그인 구현
st.sidebar.title("🔒 스팟 매니저 로그인")
selected_spot = st.sidebar.selectbox("스팟을 선택하세요", list(SPOT_CONFIG.keys()))

config = SPOT_CONFIG[selected_spot]
input_password = st.sidebar.text_input("비밀번호 입력", type="password")

if input_password == config["password"]:
    st.sidebar.success(f"🔓 {selected_spot} 인증 성공!")
    
    # 대시보드 본문 타이틀
    st.title(f"📊 {selected_spot} 근무 현황 대시보드")
    st.caption(f"조회 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 탭 구성
    tab1, tab2 = st.tabs(["👥 크루별 현황 조회", "📅 일자별 면담 기록"])
    
    with tab1:
        st.subheader("크루를 선택하여 상세 면담 기록을 확인하세요.")
        selected_employee = st.selectbox("크루 선택", list(config["employees"].keys()))
        gid = config["employees"][selected_employee]
        
        sheet_url = get_google_sheet_url(config["base_url"], gid)
        df_crew = load_data(sheet_url)
        
        if not df_crew.empty:
            # 주요 지표 시각화 (Metric)
            total_meetings = len(df_crew)
            st.row = st.columns(3)
            st.row[0].metric("총 면담 횟수", f"{total_meetings}회")
            
            if '구분' in df_crew.columns:
                regular_count = len(df_crew[df_crew['구분'].str.contains('정기', na=False)])
                issue_count = len(df_crew[df_crew['구분'].str.contains('수시|이슈', na=False)])
                st.row[1].metric("정기 면담", f"{regular_count}회")
                st.row[2].metric("이슈/수시 면담", f"{issue_count}회")
            
            st.markdown("---")
            st.dataframe(df_crew, use_container_width=True)
        else:
            st.info("해당 크루의 면담 데이터가 없거나 스프레드시트의 컬럼명을 확인해주세요.")
            
    with tab2:
        st.subheader("전체 일자별 면담 대장")
        all_data = []
        for emp_name, emp_gid in config["employees"].items():
            url = get_google_sheet_url(config["base_url"], emp_gid)
            df_emp = load_data(url)
            if not df_emp.empty:
                df_emp['크루명'] = emp_name
                all_data.append(df_emp)
                
        if all_data:
            df_total = pd.concat(all_data, ignore_index=True)
            if '일자' in df_total.columns:
                df_total = df_total.sort_values(by='일자', ascending=False)
            st.dataframe(df_total, use_container_width=True)
        else:
            st.info("조회할 수 있는 전체 데이터가 없습니다.")

elif input_password == "":
    st.info("← 왼쪽 사이드바에서 비밀번호를 입력해 주세요.")
else:
    st.sidebar.error("❌ 비밀번호가 올바르지 않습니다.")
    st.warning("정확한 스팟 매니저 비밀번호를 입력하셔야 대시보드가 활성화됩니다.")
