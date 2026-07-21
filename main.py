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
# REGION COORDINATES (시/도 및 주요 기초지자체 실제 좌표 매핑)
# -----------------------------------------------------------------------------
# 주요 기초지자체 세부 좌표 (선택 시 정확한 위치 표시용)
SUB_REGION_COORDS = {
    # 서울특별시 25개 자치구 실제 좌표
    "강남구": (37.5172, 127.0473), "강동구": (37.5301, 127.1238), "강북구": (37.6396, 127.0255),
    "강서구": (37.5509, 126.8495), "관악구": (37.4784, 126.9516), "광진구": (37.5385, 127.0823),
    "구로구": (37.4954, 126.8874), "금천구": (37.4568, 126.8952), "노원구": (37.6542, 127.0568),
    "도봉구": (37.6688, 127.0471), "동대문구": (37.5744, 127.0400), "동작구": (37.5124, 126.9393),
    "마포구": (37.5663, 126.9016), "서대문구": (37.5791, 126.9368), "서초구": (37.4837, 127.0324),
    "성동구": (37.5635, 127.0365), "성북구": (37.5894, 127.0167), "송파구": (37.5145, 127.1061),
    "양천구": (37.5169, 126.8665), "영등포구": (37.5264, 126.8962), "용산구": (37.5326, 126.9900),
    "은평구": (37.6027, 126.9291), "종로구": (37.5730, 126.9794), "중구": (37.5641, 126.9979),
    "중랑구": (37.6066, 127.0927),
}

REGION_COORDS = {
    "서울특별시": {
        "lat": 37.5665, "lng": 126.9780,
        "sub": [
            "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
            "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
            "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
        ]
    },
    "부산광역시": {
        "lat": 35.1796, "lng": 129.0756,
        "sub": ["강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구", "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구", "중구", "해운대구"]
    },
    "대구광역시": {
        "lat": 35.8714, "lng": 128.6014,
        "sub": ["군위군", "남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"]
    },
    "인천광역시": {
        "lat": 37.4563, "lng": 126.7052,
        "sub": ["강화군", "계양구", "미추홀구", "남동구", "동구", "부평구", "서구", "연수구", "옹진군", "중구"]
    },
    "광주광역시": {"lat": 35.1595, "lng": 126.8526, "sub": ["광산구", "남구", "동구", "북구", "서구"]},
    "대전광역시": {"lat": 36.3504, "lng": 127.3845, "sub": ["대덕구", "동구", "서구", "유성구", "중구"]},
    "울산광역시": {"lat": 35.5384, "lng": 129.3114, "sub": ["남구", "동구", "북구", "울주군", "중구"]},
    "세종특별자치시": {"lat": 36.4800, "lng": 127.2890, "sub": ["조치원읍", "한솔동", "도담동", "아름동", "종촌동", "고운동", "보람동", "새롬동"]},
    "경기도": {
        "lat": 37.4138, "lng": 127.5183,
        "sub": ["가평군", "고양시", "과천시", "광명시", "광주시", "구리시", "군포시", "김포시", "남양주시", "동두천시", "부천시", "성남시", "수원시", "시흥시", "안산시", "안성시", "안양시", "양주시", "양평군", "여주시", "연천군", "오산시", "용인시", "의왕시", "의정부시", "이천시", "파주시", "평택시", "포천시", "하남시", "화성시"]
    },
    "강원특별자치도": {"lat": 37.8228, "lng": 128.1555, "sub": ["강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군", "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시", "평창군", "홍천군", "화천군", "횡성군"]},
    "충청북도": {"lat": 36.6357, "lng": 127.4917, "sub": ["괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시", "증평군", "진천군", "청주시", "충주시"]},
    "충청남도": {"lat": 36.5184, "lng": 126.8000, "sub": ["계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군", "서산시", "서천군", "아산시", "예산군", "천안시", "청양군", "태안군", "홍성군"]},
    "전북특별자치도": {"lat": 35.7175, "lng": 127.1530, "sub": ["고창군", "군산시", "김제시", "남원시", "무주군", "부안군", "순창군", "완주군", "익산시", "임실군", "장수군", "전주시", "정읍시", "진안군"]},
    "전라남도": {"lat": 34.8679, "lng": 126.9910, "sub": ["강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시", "담양군", "목포시", "무안군", "보성군", "순천시", "신안군", "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군", "진도군", "함평군", "해남군", "화순군"]},
    "경상북도": {"lat": 36.5760, "lng": 128.5056, "sub": ["경산시", "경주시", "고령군", "구미시", "김천시", "문경시", "봉화군", "상주시", "성주군", "영덕군", "영양군", "영주시", "영천시", "울릉군", "울진군", "의성군", "청도군", "청송군", "칠곡군", "포항시"]},
    "경상남도": {"lat": 35.4606, "lng": 128.2132, "sub": ["거제시", "거창군", "고성군", "김해시", "남해군", "밀양시", "사천시", "산청군", "양산시", "의령군", "진주시", "창녕군", "창원시", "통영시", "하동군", "함안군", "함양군", "합천군"]},
    "제주특별자치도": {"lat": 33.4996, "lng": 126.5312, "sub": ["제주시", "서귀포시"]}
}

def get_sub_coords(sido, sub):
    """시/군/구별 정확한 기준 좌표 반환 (미등록 시 시도 기본좌표 사용)"""
    if sub in SUB_REGION_COORDS:
        return SUB_REGION_COORDS[sub]
    base = REGION_COORDS[sido]
    return (base["lat"], base["lng"])

@st.cache_data
def load_mock_data():
    np.random.seed(42)
    
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
            center_lat, center_lng = get_sub_coords(sido, sub)
            
            for i in range(np.random.randint(1, 4)):
                # 해당 구 중심 좌표 부근(약 1km 내외)으로 랜덤 생성
                lat = center_lat + np.random.uniform(-0.01, 0.01)
                lng = center_lng + np.random.uniform(-0.01, 0.01)
                
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
                    "요인명": f"{sub} {f_title}",
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
    
    accidents = []
    causes = ["노후 하수관 손상", "인근 굴착 공사 영향", "지하수 유출", "상수도 누수"]
    
    for sido, info in REGION_COORDS.items():
        for sub in info["sub"]:
            center_lat, center_lng = get_sub_coords(sido, sub)
            if np.random.rand() > 0.3:
                for i in range(np.random.randint(1, 3)):
                    lat = center_lat + np.random.uniform(-0.01, 0.01)
                    lng = center_lng + np.random.uniform(-0.01, 0.01)
                    
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

selected_sido = st.sidebar.selectbox("시/도 선택", list(REGION_COORDS.keys()))
sub_regions = REGION_COORDS[selected_sido]["sub"]
selected_sub = st.sidebar.selectbox("시/군/구 선택", ["전체"] + sub_regions)

st.sidebar.divider()

st.sidebar.subheader("🗺️ 지도 레이어 설정")
show_risk_factors = st.sidebar.checkbox("🏗️ 주요 공사/위험 요인 표시", value=True)
show_impact_radius = st.sidebar.checkbox("⭕ 지반 침하 영향 반경 표시", value=True)
show_accidents = st.sidebar.checkbox("💥 실제 사고 이력 표시", value=True)

st.sidebar.divider()

st.sidebar.subheader("📅 분석 시기 (연도 선택)")
selected_years = st.sidebar.slider(
    "공사 및 사고 분석 연도 범위",
    min_value=2022,
    max_value=2026,
    value=(2023, 2025)
)

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

# 지도 위치 및 줌 레벨 정교화
if selected_sub == "전체":
    map_center = [REGION_COORDS[selected_sido]["lat"], REGION_COORDS[selected_sido]["lng"]]
    zoom_level = 9 if "도" in selected_sido else 11
else:
    # 선택된 자치구의 정중앙 좌표 가져오기
    c_lat, c_lng = get_sub_coords(selected_sido, selected_sub)
    map_center = [c_lat, c_lng]
    zoom_level = 13  # 동/구 단위 확대를 위한 Zoom

m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")

if show_risk_factors:
    for _, row in f_risk.iterrows():
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
        
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"[위험요인] {row['요인명']} ({row['위험등급']})",
            icon=folium.Icon(color="darkpurple", icon="wrench", prefix="fa")
        ).add_to(m)
        
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
