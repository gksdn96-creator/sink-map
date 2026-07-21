import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 지반침하 위험 요인 및 사고 분석 지도",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# REGION COORDINATES & MOCK DATA GENERATOR
# -----------------------------------------------------------------------------
REGION_COORDS = {
    "서울특별시": {"lat": 37.5665, "lng": 126.9780, "sub": ["강남구", "마포구", "송파구", "영등포구", "종로구"]},
    "부산광역시": {"lat": 35.1796, "lng": 129.0756, "sub": ["해운대구", "부산진구", "사하구", "남구", "동래구"]},
    "대구광역시": {"lat": 35.8714, "lng": 128.6014, "sub": ["중구", "동구", "수성구", "달서구"]},
    "인천광역시": {"lat": 37.4563, "lng": 126.7052, "sub": ["남동구", "부평구", "서구", "연수구"]},
    "광주광역시": {"lat": 35.1595, "lng": 126.8526, "sub": ["서구", "북구", "광산구", "동구"]},
    "대전광역시": {"lat": 36.3504, "lng": 127.3845, "sub": ["유성구", "서구", "중구", "대덕구"]},
    "울산광역시": {"lat": 35.5384, "lng": 129.3114, "sub": ["남구", "중구", "북구", "울주군"]},
    "세종특별자치시": {"lat": 36.4800, "lng": 127.2890, "sub": ["세종시"]},
    "경기도": {"lat": 37.4138, "lng": 127.5183, "sub": ["수원시", "성남시", "고양시", "용인시", "부천시"]},
    "강원특별자치도": {"lat": 37.8228, "lng": 128.1555, "sub": ["춘천시", "원주시", "강릉시", "속초시"]},
    "충청북도": {"lat": 36.6357, "lng": 127.4917, "sub": ["청주시", "충주시", "제천시"]},
    "충청남도": {"lat": 36.5184, "lng": 126.8000, "sub": ["천안시", "아산시", "서산시"]},
    "전북특별자치도": {"lat": 35.7175, "lng": 127.1530, "sub": ["전주시", "익산시", "군산시"]},
    "전라남도": {"lat": 34.8679, "lng": 126.9910, "sub": ["목포시", "여수시", "순천시"]},
    "경상북도": {"lat": 36.5760, "lng": 128.5056, "sub": ["포항시", "구미시", "경주시"]},
    "경상남도": {"lat": 35.4606, "lng": 128.2132, "sub": ["창원시", "김해시", "양산시"]},
    "제주특별자치도": {"lat": 33.4996, "lng": 126.5312, "sub": ["제주시", "서귀포시"]}
}

@st.cache_data
def load_mock_data():
    np.random.seed(42)
    
    # 1. 지반침하 주요 위험 요인 (대형 공사, 건물 신축, 노후관 등)
    risk_factors = []
    factor_types = [
        ("초고층 아파트 지하 굴착", "대형 굴착공사", 85, 300),
        ("대형 백화점/복합쇼핑몰 신축", "대형 굴착공사", 75, 250),
        ("노후 상하수도관 정비/교체", "관로 노후화", 60, 150),
        ("지하철/지하차도 터널 굴착", "특수 터널공사", 90, 400),
        ("지하수 과다 양수 현장", "지하수 변동", 70, 200)
    ]
    
    for sido, info in REGION_COORDS.items():
        for sub in info["sub"]:
            for i in range(np.random.randint(2, 5)):
                lat = info["lat"] + np.random.uniform(-0.035, 0.035)
                lng = info["lng"] + np.random.uniform(-0.035, 0.035)
                
                f_title, f_cat, base_score, base_radius = factor_types[np.random.choice(len(factor_types))]
                
                start_year = np.random.choice([2023, 2024, 2025])
                start_month = np.random.randint(1, 13)
                duration_months = np.random.randint(6, 36)
                
                start_date = datetime(start_year, start_month, 1)
                end_date = start_date + pd.DateOffset(months=duration_months)
                
                impact_score = min(100, max(30, base_score + np.random.randint(-15, 15)))
                impact_radius = max(100, base_radius + np.random.randint(-50, 100))
                
                risk_factors.append({
                    "요인ID": f"RF-{sido[:2]}-{np.random.randint(1000, 9999)}",
                    "시도": sido,
                    "시군구": sub,
                    "요인명": f_title,
                    "분류": f_cat,
                    "공사_영향시작일": start_date.strftime("%Y-%m-%d"),
                    "공사_영향종료일": end_date.strftime("%Y-%m-%d"),
                    "공사연도": start_year,
                    "영향력_점수": impact_score,
                    "영향_반경_m": impact_radius,
                    "위험등급": "매우높음" if impact_score >= 80 else ("높음" if impact_score >= 65 else "보통"),
                    "lat": lat,
                    "lng": lng
                })
                
    df_risk = pd.DataFrame(risk_factors)
    
    # 2. 실제 지반침하 사고 이력 데이터
    accidents = []
    causes = ["노후 하수관 손상", "인근 굴착 공사 영향", "지하수 유출", "상수도 누수"]
    
    for sido, info in REGION_COORDS.items():
        for sub in info["sub"]:
            for i in range(np.random.randint(1, 3)):
                lat = info["lat"] + np.random.uniform(-0.03, 0.03)
                lng = info["lng"] + np.random.uniform(-0.03, 0.03)
                
                accidents.append({
                    "사고ID": f"ACC-{np.random.randint(10000, 99999)}",
                    "시도": sido,
                    "시군구": sub,
                    "발생일자": f"202{np.random.randint(2, 6)}-0{np.random.randint(1, 10)}-{np.random.randint(10, 28)}",
                    "발생연도": np.random.choice([2022, 2023, 2024, 2025]),
                    "원인": np.random.choice(causes),
                    "침하깊이_m": round(np.random.uniform(0.5, 3.8), 1),
                    "위험규모": np.random.choice(["소형", "중형", "대형"]),
                    "lat": lat,
                    "lng": lng
                })
    df_accidents = pd.DataFrame(accidents)
    
    return df_risk, df_accidents

df_risk, df_accidents = load_mock_data()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROL & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.title("🔍 위험 요인 & 사고 탐색")

# 1. 지역 선택
selected_sido = st.sidebar.selectbox("시/도 선택", list(REGION_COORDS.keys()))
sub_regions = REGION_COORDS[selected_sido]["sub"]
selected_sub = st.sidebar.selectbox("시/군/구 선택", ["전체"] + sub_regions)

st.sidebar.divider()

# 2. 지도 레이어 설정
st.sidebar.subheader("🗺️ 지도 레이어 설정")
show_risk_factors = st.sidebar.checkbox("🏗️ 주요 공사/위험 요인 표시", value=True)
show_impact_radius = st.sidebar.checkbox("⭕ 지반 침하 영향 반경 표시", value=True)
show_accidents = st.sidebar.checkbox("💥 실제 사고 이력 표시", value=True)

st.sidebar.divider()

# 3. 기간/시기 필터링
st.sidebar.subheader("📅 분석 시기 (연도 선택)")
selected_years = st.sidebar.slider(
    "공사 및 사고 분석 연도 범위",
    min_value=2022,
    max_value=2026,
    value=(2023, 2025)
)

# 데이터 필터링
f_risk = df_risk[
    (df_risk["시도"] == selected_sido) &
    (df_risk["공사연도"] >= selected_years[0]) &
    (df_risk["공사연도"] <= selected_years[1])
]

f_accidents = df_accidents[
    (df_accidents["시도"] == selected_sido) &
    (df_accidents["발생연도"] >= selected_years[0]) &
    (df_accidents["발생연도"] <= selected_years[1])
]

if selected_sub != "전체":
    f_risk = f_risk[f_risk["시군구"] == selected_sub]
    f_accidents = f_accidents[f_accidents["시군구"] == selected_sub]

# -----------------------------------------------------------------------------
# MAIN DASHBOARD HEADER
# -----------------------------------------------------------------------------
st.title("🏗️ 전국 지반침하 위험 요인 & 영향력 분석 지도")
st.markdown("""
고층 아파트/백화점 신축 굴착 공사, 지하철 공사, 상하수도 관로 노후화 등 **지반침하 관련 주요 위험 요인의 영향력과 시기**, 그리고 **실제 사고 이력**을 종합 모니터링합니다.
""")

# 핵심 지표 메트릭
c1, c2, c3, c4 = st.columns(4)
c1.metric("탐색 지역", f"{selected_sido} {selected_sub if selected_sub != '전체' else ''}")
c2.metric("위험 공사/요인 현황", f"{len(f_risk)} 건")
c3.metric("평균 침하 영향력 점수", f"{f_risk['영향력_점수'].mean():.1f} / 100점" if not f_risk.empty else "0점")
c4.metric("기간 내 사고 이력", f"{len(f_accidents)} 건")

st.divider()

# -----------------------------------------------------------------------------
# MAP RENDERING
# -----------------------------------------------------------------------------
st.subheader("🗺️ 지반침하 위험 영향도 및 사고 지도")

if selected_sub == "전체":
    map_center = [REGION_COORDS[selected_sido]["lat"], REGION_COORDS[selected_sido]["lng"]]
    zoom_level = 11
else:
    lat_mean = f_risk["lat"].mean() if not f_risk.empty else REGION_COORDS[selected_sido]["lat"]
    lng_mean = f_risk["lng"].mean() if not f_risk.empty else REGION_COORDS[selected_sido]["lng"]
    map_center = [lat_mean, lng_mean]
    zoom_level = 13

m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")

# 1. 위험 요인(공사/대형건물) 및 영향 반경 마커
if show_risk_factors:
    for _, row in f_risk.iterrows():
        # 영향력별 색상
        color = "#ff3333" if row["위험등급"] == "매우높음" else ("#ff9900" if row["위험등급"] == "높음" else "#3399ff")
        
        popup_html = f"""
        <div style='width:220px;'>
            <h4><b>{row['요인명']}</b></h4>
            <b>분류:</b> {row['분류']}<br>
            <b>위험등급:</b> <b style='color:{color};'>{row['위험등급']}</b> ({row['영향력_점수']}점)<br>
            <b>영향 범위:</b> 반경 {row['영향_반경_m']}m<br>
            <b>공사/영향 기간:</b><br>{row['공사_영향시작일']} ~ {row['공사_영향종료일']}<br>
            <b>위치:</b> {row['시군구']}
        </div>
        """
        
        # 공사현장 위치 마커
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"[위험요인] {row['요인명']} ({row['위험등급']})",
            icon=folium.Icon(color="darkpurple", icon="wrench", prefix="fa")
        ).add_to(m)
        
        # 지반 침하 영향 반경 (Circle)
        if show_impact_radius:
            folium.Circle(
                location=[row["lat"], row["lng"]],
                radius=row["영향_반경_m"],
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.2,
                popup=f"영향 반경: {row['영향_반경_m']}m ({row['요인명']})"
            ).add_to(m)

# 2. 실제 사고 이력 마커
if show_accidents:
    for _, row in f_accidents.iterrows():
        popup_html = f"""
        <div style='width:200px;'>
            <h4 style='color:red;'><b>💥 지반침하 사고</b></h4>
            <b>발생일자:</b> {row['발생일자']}<br>
            <b>추정원인:</b> {row['원인']}<br>
            <b>침하 깊이:</b> {row['침하깊이_m']}m<br>
            <b>위치:</b> {row['시도']} {row['시군구']}
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"[사고발생] {row['발생일자']} - {row['원인']}",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
        ).add_to(m)

st_folium(m, width="100%", height=530)

# -----------------------------------------------------------------------------
# DETAILED ANALYTICS & TIMELINE
# -----------------------------------------------------------------------------
st.divider()
st.subheader("📊 위험 요인 시기(기간) 및 침하 영향력 분석")

tab1, tab2, tab3 = st.tabs(["🏗️ 공사/위험 요인 및 영향력 목록", "📈 영향력 점수 및 시기 분석", "💥 사고 발생 데이터"])

with tab1:
    if not f_risk.empty:
        st.dataframe(
            f_risk[["요인명", "분류", "위험등급", "영향력_점수", "영향_반경_m", "공사_영향시작일", "공사_영향종료일", "시군구"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("선택한 조건에 해당하는 위험 요인 데이터가 없습니다.")

with tab2:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if not f_risk.empty:
            fig_bar = px.bar(
                f_risk,
                x="요인명",
                y="영향력_점수",
                color="위험등급",
                title="위험 요인별 침하 영향력 점수 (100점 만점)",
                hover_data=["공사_영향시작일", "공사_영향종료일"],
                color_discrete_map={"매우높음": "#ff3333", "높음": "#ff9900", "보통": "#3399ff"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    with col_chart2:
        if not f_risk.empty:
            fig_scatter = px.scatter(
                f_risk,
                x="영향력_점수",
                y="영향_반경_m",
                size="영향_반경_m",
                color="분류",
                hover_name="요인명",
                title="영향력 점수 vs 지반 침하 영향 반경(m)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

with tab3:
    if not f_accidents.empty:
        st.dataframe(
            f_accidents[["사고ID", "발생일자", "원인", "침하깊이_m", "위험규모", "시군구"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("선택한 조건에 해당하는 사고 이력이 없습니다.")
