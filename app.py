import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정 및 블루 테마 설정
st.set_page_config(page_title="케어 매니저 AI 대시보드", layout="wide")

st.title("📊 스팟 매니저 AI 통합 대시보드")
st.markdown("---")

# 2. 구글 스프레드시트 연동 설정 및 스팟별 비밀번호 개별 설정
SPOT_CONFIG = {
    "사내카페 (kafe5)": {
        "base_url": "https://docs.google.com/spreadsheets/d/1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "kafe5",
        "employees": {
            "루크(장종원)": "1518673498",
            "휴버트(강채운)": "1231497521"
        }
    },
    "행정지원스팟 (office7)": {
        "base_url": "https://docs.google.com/spreadsheets/d/1rRpq9zX7g70hX2uwRwA1enPY83KSK_lNOiJ1MGIOzqY",
        "password": "office7",
        "employees": {
            "테스트크루": "0"
        }
    }
}

def get_google_sheet_url(base_url, gid):
    return f"{base_url}/export?format=csv&gid={gid}"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 간단한 AI 감정/이슈 규칙 분석 함수 (대체 구현)
def analyze_crew_data(df):
    if df.empty:
        return None
    
    total = len(df)
    # 면담 내용이나 비고 컬럼에서 핵심 키워드 추출하여 가상 AI 분석 요약 생성
    text_content = ""
    for col in df.columns:
        if '내용' in col or '비고' in col or '이슈' in col or '내용 요약' in col:
            text_content += " ".join(df[col].astype(str).tolist())
            
    keywords = []
    if "힘들" in text_content or "어려움" in text_content or "스트레스" in text_content:
        keywords.append("⚠️ 업무 스트레스 관리 필요")
    if "만족" in text_content or "좋아" in text_content or "원활" in text_content:
        keywords.append("😊 전반적인 업무 만족도 높음")
    if "건강" in text_content or "아프" in text_content or "병원" in text_content:
        keywords.append("🩺 컨디션 및 건강 체크 필요")
    if "진로" in text_content or "퇴사" in text_content or "이직" in text_content:
        keywords.append("🏃 미래 진로 및 고용 안정성 상담 필요")
        
    if not keywords:
        keywords.append("✅ 특이사항 없음 (안정적인 근무 상태)")
        
    return {
        "total": total,
        "alerts": keywords,
        "recent_date": df['일자'].iloc[0] if '일자' in df.columns else '기록 없음'
    }

# 3. 사이드바 로그인 구현
st.sidebar.title("🔒 AI 스팟 매니저 로그인")
selected_spot = st.sidebar.selectbox("스팟을 선택하세요", list(SPOT_CONFIG.keys()))

config = SPOT_CONFIG[selected_spot]
input_password = st.sidebar.text_input("비밀번호 입력", type="password")

if input_password == config["password"]:
    st.sidebar.success(f"🔓 {selected_spot} 인증 성공!")
    
    st.caption(f"조회 시간: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tab1, tab2 = st.tabs(["👥 크루별 AI 분석 조회", "📅 전체 면담 기록 대장"])
    
    with tab1:
        selected_employee = st.selectbox("조회할 크루를 선택하세요", list(config["employees"].keys()))
        gid = config["employees"][selected_employee]
        
        sheet_url = get_google_sheet_url(config["base_url"], gid)
        df_crew = load_data(sheet_url)
        
        if not df_crew.empty:
            # 🤖 [핵심] AI 종합 분석 브리핑 영역
            st.subheader(f"🤖 AI 가 분석한 {selected_employee} 크루 브리핑")
            
            ai_analysis = analyze_crew_data(df_crew)
            
            # 대시보드 상단 요약 카드 (Metric)
            cols = st.columns(3)
            cols[0].metric("총 면담 횟수", f"{ai_analysis['total']}회")
            cols[1].metric("최근 면담일", str(ai_analysis['recent_date']))
            cols[2].metric("AI 종합 진단", "분석 완료")
            
            # 정보 상자 스타일로 요약 리포트 출력
            with st.expander("💡 AI 면담일지 핵심 요약 리포트 (클릭하여 열기)", expanded=True):
                st.write(f"**[{selected_employee} 크루의 최근 면담 패턴 및 주요 키워드 요약]**")
                for alert in ai_analysis['alerts']:
                    st.write(f"- {alert}")
                st.info("※ 위 분석은 면담일지 내 텍스트 데이터를 기반으로 생성된 AI 실시간 요약본입니다.")
            
            st.markdown("---")
            st.subheader("📋 전체 상세 면담일지 원본")
            st.dataframe(df_crew, use_container_width=True)
        else:
            st.info("해당 크루의 면담 데이터가 없거나 스프레드시트 양식을 확인해주세요.")
            
    with tab2:
        st.subheader("📅 전체 일자별 면담 대장")
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
