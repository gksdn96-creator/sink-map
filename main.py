import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="전국 지반침하 위험지역 지도",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# DUMMY DATA GENERATOR (실제 운영 시 DB 또는 API 연결 구간)
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
    """시/도 및 시/군/구별 지반침하 데이터 생성 함수"""
    np.random.seed(42)
    
    # 1. 시/도 단위 요약 데이터
    sido_summary = []
    for sido, info in REGION_COORDS.items():
        sido_summary.append({
            "시도": sido,
            "lat": info["lat"],
            "lng": info["lng"],
            "위험도등급": np.random.choice(["관심", "주의", "경계", "심각"], p=[0.3, 0.4, 0.2, 0.1]),
            "공사현장수": np.random.randint(5, 50),
            "최근3년_사고건수": np.random.randint(0, 15)
        })
    df_sido = pd.DataFrame(sido_summary)

    # 2. 상세 사고 이력 및 공사구역 데이터
    accidents = []
    causes = ["노후 하수관 손상", "굴착 공사 부실", "지하수 유출", "상수도관 누수"]
    
    for sido, info in REGION_COORDS.items():
        for sub in info["sub"]:
            # 지역별 1~3개의 상세 기록 생성
            for i in range(np.random.randint(1, 4)):
                # 중심점 근처에 노이즈를 주어 좌표 생성
                lat_offset = np.random.uniform(-0.03, 0.03)
                lng_offset = np.random.uniform(-0.03, 0.03)
                
                accidents.append({
                    "시도": sido,
                    "시군구": sub,
                    "위험도": np.random.choice(["낮음", "보통", "높음", "매우 높음"]),
                    "사고일자": f"202{np.random.randint(3, 7)}-0{np.random.randint(1, 10)}-{np.random.randint(10, 28)}",
                    "원인": np.random.choice(causes),
                    "침하규모(m)": round(np.random.uniform(0.5, 3.5), 1),
                    "인근공사현황": np.random.choice(["지하철 굴착 공사", "건축 기초 공사", "관로 교체 공사", "없음"]),
                    "lat": info["lat"] + lat_offset,
                    "lng": info["lng"] + lng_offset
                })
    df_accidents = pd.DataFrame(accidents)
    
    return df_sido, df_accidents

df_sido, df_accidents = load_mock_data()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROL
# -----------------------------------------------------------------------------
st.sidebar.title("🔍 세부 지역 탐색")
st.sidebar.markdown("시/도 및 하위 행정구역을 선택하여 상세 위험도와 사고 이력을 확인하세요.")

selected_sido = st.sidebar.selectbox("시/도 선택", list(REGION_COORDS.keys()))

sub_regions = REGION_COORDS[selected_sido]["sub"]
selected_sub = st.sidebar.selectbox("시/군/구 선택", ["전체"] + sub_regions)

st.sidebar.divider()

# 사이드바 하부 정보 표시 (선택된 시/군/구 분석)
st.sidebar.subheader(f"📍 {selected_sido} {selected_sub if selected_sub != '전체' else ''} 현황")

filtered_df = df_accidents[df_accidents["시도"] == selected_sido]
if selected_sub != "전체":
    filtered_df = filtered_df[filtered_df["시군구"] == selected_sub]

st.sidebar.metric("총 등록된 사고/위험건수", f"{len(filtered_df)} 건")
high_risk_count = len(filtered_df[filtered_df["위험도"].isin(["높음", "매우 높음"])])
st.sidebar.metric("고위험군 구역 수", f"{high_risk_count} 개", delta_color="inverse")

with st.sidebar.expander("📋 세부 이력 목록 보기"):
    st.dataframe(
        filtered_df[["시군구", "위험도", "사고일자", "원인"]],
        hide_index=True,
        use_container_width=True
    )

# -----------------------------------------------------------------------------
# MAIN PAGE LAYOUT
# -----------------------------------------------------------------------------
st.title("⚠️ 전국 지반침하 위험지역 및 사고 이력 지도")
st.markdown("""
전국 주요 지자체의 지반공사 현황, 지반침하 위험도, 과거 싱크홀 및 지반침하 발생 기록을 시각화한 모니터링 시스템입니다.
""")

# 상단 요약 카드
col1, col2, col3, col4 = st.columns(4)
col1.metric("전국 분석 시/도", f"{len(REGION_COORDS)} 개 구역")
col2.metric("총 수집 사고 이력", f"{len(df_accidents)} 건")
col3.metric("최다 발생 원인", df_accidents["원인"].mode()[0])
col4.metric("평균 침하 규모", f"{df_accidents['침하규모(m)'].mean():.2f} m")

st.divider()

# -----------------------------------------------------------------------------
# MAP RENDERING
# -----------------------------------------------------------------------------
st.subheader("🗺️ 전국 및 지역별 지반침하 지도")

# 선택 지역에 따라 지도 중심점 및 줌 레벨 결정
if selected_sub == "전체":
    map_center = [REGION_COORDS[selected_sido]["lat"], REGION_COORDS[selected_sido]["lng"]]
    zoom_level = 10
else:
    # 선택된 시군구 데이터의 평균 위치로 이동
    map_center = [filtered_df["lat"].mean(), filtered_df["lng"].mean()]
    zoom_level = 12

m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")

# 위험도별 마커 색상 지정
color_map = {
    "낮음": "green",
    "보통": "blue",
    "높음": "orange",
    "매우 높음": "red"
}

# 지도에 사고/위험 지점 마커 추가
for _, row in filtered_df.iterrows():
    popup_content = f"""
    <div style='width:200px;'>
        <h4><b>{row['시도']} {row['시군구']}</b></h4>
        <b>위험도:</b> <span style='color:{color_map[row['위험도']]};'>{row['위험도']}</span><br>
        <b>발생일자:</b> {row['사고일자']}<br>
        <b>원인:</b> {row['원인']}<br>
        <b>침하 깊이:</b> {row['침하규모(m)']}m<br>
        <b>인근 공사:</b> {row['인근공사현황']}
    </div>
    """
    
    folium.Marker(
        location=[row["lat"], row["lng"]],
        popup=folium.Popup(popup_content, max_width=250),
        tooltip=f"[{row['위험도']}] {row['시군구']} - {row['원인']}",
        icon=folium.Icon(color=color_map[row["위험도"]], icon="warning-sign")
    ).add_to(m)

# Streamlit에 Folium 지도 출력
st_data = st_folium(m, width="100%", height=500)

# -----------------------------------------------------------------------------
# DETAILED DATA TABLE & ANALYTICS
# -----------------------------------------------------------------------------
st.divider()
st.subheader(f"📊 {selected_sido} {selected_sub if selected_sub != '전체' else ''} 상세 데이터")

tab1, tab2 = st.tabs(["사고 및 위험지점 데이터", "원인별 통계"])

with tab1:
    st.dataframe(
        filtered_df.drop(columns=["lat", "lng"]),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    if not filtered_df.empty:
        chart_data = filtered_df["원인"].value_counts().reset_index()
        chart_data.columns = ["원인", "건수"]
        st.bar_chart(chart_data, x="원인", y="건수")
    else:
        st.info("해당 지역의 데이터가 없습니다.")
