# -*- coding: utf-8 -*-
"""
전국 지반침하(싱크홀) 위험지도
--------------------------------
- 지도에서 지역(시·도)을 클릭하면 해당 지역의 위험도, 최근 5년간 사고 건수,
  실제 지반침하 사고 이력을 볼 수 있는 Streamlit 앱입니다.
- 기본 데이터는 국토교통부 통계(2020~2024년 17개 시·도 지반침하 발생건수) 및
  언론에 보도된 실제 사고 사례를 참고해 구성한 "샘플/예시 데이터"입니다.
  일부 시·도는 세부 통계가 공개돼 있지 않아 추정치(estimated=True)로 채워두었으니,
  실제 서비스에 쓰실 때는 아래 "실시간 공공데이터 연동" 섹션을 참고해 진짜 데이터로 교체하세요.

배포 방법 (Streamlit Community Cloud):
1. GitHub 저장소를 하나 만들고 이 파일을 app.py 로, requirements.txt 를 함께 올립니다.
2. https://share.streamlit.io 에서 New app → 저장소/브랜치/app.py 선택 → Deploy.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# ----------------------------------------------------------------------
# 기본 설정
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="전국 지반침하 위험지도",
    page_icon="🕳️",
    layout="wide",
)

RISK_COLORS = {
    1: "#2ecc71",  # 매우낮음 - 초록
    2: "#a8d92e",  # 낮음 - 연두
    3: "#f1c40f",  # 보통 - 노랑
    4: "#e67e22",  # 높음 - 주황
    5: "#e74c3c",  # 매우높음 - 빨강
}
RISK_LABELS = {1: "매우낮음", 2: "낮음", 3: "보통", 4: "높음", 5: "매우높음"}


# ----------------------------------------------------------------------
# 지역 기본 데이터 (17개 시·도, 중심 좌표는 근사값)
# 최근 5년(2020~2024) 지반침하 사고 건수:
#   - 경기(173건), 광주(108건), 부산(89건), 서울(85건)은 국토교통부 통계로 확인된 값
#     (17개 시·도 합계 867건 중 상위 4개 지역, 국회입법조사처 자료 재인용)
#   - 나머지 13개 시·도는 세부 수치가 공개돼 있지 않아 균등 추정치(estimated=True)를 사용
# ----------------------------------------------------------------------
REGIONS = [
    {"name": "서울특별시", "lat": 37.5665, "lon": 126.9780, "incidents_5y": 85, "estimated": False,
     "top_cause": "하수관 손상 > 다짐(되메우기) 불량"},
    {"name": "부산광역시", "lat": 35.1796, "lon": 129.0756, "incidents_5y": 89, "estimated": False,
     "top_cause": "하수관 손상 > 다짐(되메우기) 불량"},
    {"name": "대구광역시", "lat": 35.8714, "lon": 128.6014, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "인천광역시", "lat": 37.4563, "lon": 126.7052, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "광주광역시", "lat": 35.1595, "lon": 126.8526, "incidents_5y": 108, "estimated": False,
     "top_cause": "하수관 손상 > 다짐(되메우기) 불량"},
    {"name": "대전광역시", "lat": 36.3504, "lon": 127.3845, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "울산광역시", "lat": 35.5384, "lon": 129.3114, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "세종특별자치시", "lat": 36.4800, "lon": 127.2890, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "경기도", "lat": 37.4138, "lon": 127.5183, "incidents_5y": 173, "estimated": False,
     "top_cause": "하수관 손상 > 굴착공사 부실"},
    {"name": "강원특별자치도", "lat": 37.8228, "lon": 128.1555, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치, 석회암 지대 주의)"},
    {"name": "충청북도", "lat": 36.6357, "lon": 127.4917, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "충청남도", "lat": 36.5184, "lon": 126.8000, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "전북특별자치도", "lat": 35.7175, "lon": 127.1530, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "전라남도", "lat": 34.8161, "lon": 126.4630, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "경상북도", "lat": 36.4919, "lon": 128.8889, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "경상남도", "lat": 35.4606, "lon": 128.2132, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치)"},
    {"name": "제주특별자치도", "lat": 33.4996, "lon": 126.5312, "incidents_5y": 32, "estimated": True,
     "top_cause": "미상 (추정치, 화산암 지대 주의)"},
]


def score_to_level(incidents: int) -> int:
    """최근 5년 사고 건수를 5단계 위험도로 변환"""
    if incidents < 20:
        return 1
    elif incidents < 40:
        return 2
    elif incidents < 70:
        return 3
    elif incidents < 120:
        return 4
    else:
        return 5


for r in REGIONS:
    r["risk_level"] = score_to_level(r["incidents_5y"])


REGION_DF = pd.DataFrame(REGIONS)


# ----------------------------------------------------------------------
# 실제 보도된 지반침하 사고 이력 (샘플)
# 정확한 발생 일자·좌표가 공개되지 않은 사례는 "확인 필요"로 표시했습니다.
# 실서비스에서는 안전신문고/재난안전데이터공유플랫폼(safetydata.go.kr) 등의
# 실제 사고 데이터로 교체하시길 권장합니다.
# ----------------------------------------------------------------------
INCIDENTS = [
    {
        "region": "서울특별시",
        "title": "서대문구 연희동 성산로 싱크홀",
        "date": "2024-08-29",
        "desc": "성산대교 방면 성산로 모래내고가차도 부근에서 가로 6m·세로 4m·깊이 2.5m 규모의 지반침하가 발생해 주행 중이던 차량이 전복되는 사고가 있었습니다.",
        "source": "언론 보도 종합",
    },
    {
        "region": "서울특별시",
        "title": "강동구 명일동 대명초사거리 인근 지반침하",
        "date": "확인 필요",
        "desc": "강동구 명일동 학교 인근 도로에서 지반침하가 발생했습니다. 정확한 발생 일자는 별도 확인이 필요합니다.",
        "source": "언론 보도 종합",
    },
    {
        "region": "인천광역시",
        "title": "서울지하철 7호선 청라 연장구간 지반침하",
        "date": "공사 기간 중",
        "desc": "7호선 청라 연장 공사 구간에서 지반침하가 발생해 개통이 지연된 사례입니다.",
        "source": "언론 보도 종합",
    },
    {
        "region": "경기도",
        "title": "수도권전철 8호선 별내선 구간 지반침하",
        "date": "공사 기간 중",
        "desc": "8호선 별내선 연장 공사 구간에서 지반침하가 발생해 개통이 지연된 사례입니다.",
        "source": "언론 보도 종합",
    },
    {
        "region": "경상남도",
        "title": "부전~마산 복선전철 터널 붕괴 사고",
        "date": "확인 필요",
        "desc": "부산~창원(마산) 구간 복선전철 터널 공사 중 붕괴 사고가 발생한 사례입니다.",
        "source": "언론 보도 종합",
    },
]
INCIDENT_DF = pd.DataFrame(INCIDENTS)

# 최근 10년 전국 지반침하 사고 추이 (국토교통부 통계, 일부 연도는 보도자료 인용)
NATIONAL_TREND = pd.DataFrame({
    "연도": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "전국 사고건수": [186, None, None, 338, 193, None, None, None, None, None],
})


# ----------------------------------------------------------------------
# (선택) 공공데이터포털 실시간 연동 - 베타
# 전국지반침하정보표준데이터 API를 사용하려면 data.go.kr에서 서비스키를 발급받아
# 아래 함수에 입력하세요. 실제 응답 스키마는 공공데이터포털 문서를 참고해
# 파싱 로직(json 파싱 부분)을 상황에 맞게 수정해야 할 수 있습니다.
# ----------------------------------------------------------------------
def fetch_live_data(service_key: str):
    url = "http://apis.data.go.kr/1611000/undergroundsafetyinfo/getImpatEvalutionList"
    params = {
        "serviceKey": service_key,
        "type": "json",
        "numOfRows": 100,
        "pageNo": 1,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}


# ----------------------------------------------------------------------
# 사이드바
# ----------------------------------------------------------------------
st.sidebar.title("🕳️ 전국 지반침하 위험지도")
st.sidebar.caption("지도를 클릭하거나 아래에서 지역을 선택해 상세 정보를 확인하세요.")

region_names = REGION_DF["name"].tolist()
selected_from_list = st.sidebar.selectbox("지역 선택 (지도 클릭 대신 사용 가능)", ["-- 선택 안 함 --"] + region_names)

st.sidebar.divider()
st.sidebar.subheader("⚙️ 실시간 공공데이터 연동 (선택, 베타)")
service_key = st.sidebar.text_input("공공데이터포털 서비스키 입력", type="password")
if service_key:
    if st.sidebar.button("실시간 데이터 불러오기"):
        with st.sidebar:
            with st.spinner("불러오는 중..."):
                data = fetch_live_data(service_key)
            st.json(data)
st.sidebar.caption(
    "전국지반침하정보표준데이터: data.go.kr 에서 '지반침하' 검색 후 서비스키를 발급받아 입력하세요. "
    "응답 형식은 기관 사정에 따라 바뀔 수 있어 별도 파싱 수정이 필요할 수 있습니다."
)

st.sidebar.divider()
st.sidebar.caption(
    "⚠️ 이 앱의 지역별 위험도·사고 건수는 일부만 실제 통계이며 나머지는 예시(추정)값입니다. "
    "실제 의사결정에는 국토교통부·지자체의 공식 자료를 확인하세요."
)


# ----------------------------------------------------------------------
# 메인 화면
# ----------------------------------------------------------------------
st.title("🕳️ 전국 지반침하 위험지역 지도")
st.markdown(
    "지도의 원을 클릭하면 해당 지역의 **위험도**, **최근 5년 사고 건수**, "
    "**실제 지반침하 사고 이력**을 아래에서 확인할 수 있습니다."
)

col_stat1, col_stat2, col_stat3 = st.columns(3)
col_stat1.metric("최근 5년(2020~2024) 전국 사고", "867건")
col_stat2.metric("최근 10년(2015~2024) 전국 사고", "2,119건 (연평균 약 212건)")
col_stat3.metric("사고 최다 지역(5년)", "경기도 173건")

st.caption("출처: 국토교통부 통계 재인용(국회입법조사처 자료). 세부 수치는 갱신 시점에 따라 달라질 수 있습니다.")

st.divider()

# 지도 생성
m = folium.Map(location=[36.4, 127.9], zoom_start=7, tiles="CartoDB positron")

for r in REGIONS:
    level = r["risk_level"]
    color = RISK_COLORS[level]
    popup_html = (
        f"<b>{r['name']}</b><br>"
        f"위험도: {RISK_LABELS[level]}<br>"
        f"최근 5년 사고건수: {r['incidents_5y']}건"
        f"{' (추정치)' if r['estimated'] else ''}<br>"
        f"주요 원인: {r['top_cause']}"
    )
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=8 + level * 3,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.75,
        weight=2,
        tooltip=r["name"],
        popup=folium.Popup(popup_html, max_width=250),
    ).add_to(m)

# 범례
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index:9999; background: white;
padding: 10px 14px; border-radius: 8px; border: 1px solid #ccc; font-size: 13px;">
<b>위험도</b><br>
<span style="color:#e74c3c;">●</span> 매우높음&nbsp;
<span style="color:#e67e22;">●</span> 높음&nbsp;
<span style="color:#f1c40f;">●</span> 보통&nbsp;
<span style="color:#a8d92e;">●</span> 낮음&nbsp;
<span style="color:#2ecc71;">●</span> 매우낮음
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

map_data = st_folium(m, width=None, height=520, returned_objects=["last_object_clicked_tooltip"])

# 클릭된 지역 결정 (지도 클릭 우선, 없으면 사이드바 선택값 사용)
clicked_region = None
if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_region = map_data["last_object_clicked_tooltip"]
elif selected_from_list != "-- 선택 안 함 --":
    clicked_region = selected_from_list

st.divider()

# ----------------------------------------------------------------------
# 상세 패널
# ----------------------------------------------------------------------
if clicked_region:
    info = REGION_DF[REGION_DF["name"] == clicked_region].iloc[0]
    level = int(info["risk_level"])

    st.header(f"📍 {clicked_region}")

    c1, c2, c3 = st.columns(3)
    c1.metric("위험도", RISK_LABELS[level])
    c2.metric("최근 5년 사고건수", f"{int(info['incidents_5y'])}건" + (" (추정치)" if info["estimated"] else ""))
    c3.metric("주요 원인", info["top_cause"])

    if info["estimated"]:
        st.info(
            "이 지역은 세부 통계가 공개되지 않아 예시(추정) 값을 사용하고 있습니다. "
            "실제 데이터로 교체하려면 사이드바의 공공데이터 연동 기능을 이용하세요."
        )

    st.subheader("📋 실제 지반침하 사고 이력")
    region_incidents = INCIDENT_DF[INCIDENT_DF["region"] == clicked_region]
    if len(region_incidents) == 0:
        st.write("등록된 사고 이력 샘플이 없습니다. (실제로 사고가 없었다는 의미는 아닙니다)")
    else:
        for _, inc in region_incidents.iterrows():
            with st.container(border=True):
                st.markdown(f"**{inc['title']}**  ·  {inc['date']}")
                st.write(inc["desc"])
                st.caption(f"출처: {inc['source']}")

    st.subheader("📊 전국 지역별 최근 5년 사고건수 비교")
    chart_df = REGION_DF[["name", "incidents_5y"]].set_index("name")
    st.bar_chart(chart_df)

else:
    st.info("👆 지도의 원을 클릭하거나 사이드바에서 지역을 선택하면 상세 정보가 표시됩니다.")

st.divider()
with st.expander("ℹ️ 데이터 안내 및 실제 데이터로 교체하는 방법"):
    st.markdown(
        """
- **국가 통계**: 국토교통부 지반침하 발생 현황(2015~2024, 국회입법조사처 자료 재인용)
- **지역별 사고건수**: 경기(173건)·광주(108건)·부산(89건)·서울(85건)은 최근 5년(2020~2024) 공개 통계이며,
  나머지 13개 시·도는 세부 수치가 없어 균등 추정치를 넣어두었습니다.
- **사고 이력 샘플**: 언론에 보도된 실제 사고 몇 건을 요약했습니다. 전수 데이터가 아닙니다.
- **실제 데이터로 교체하려면**:
  1. [공공데이터포털](https://www.data.go.kr) 에서 '전국지반침하정보표준데이터' 또는
     '지반침하 위험도평가' 데이터를 신청해 서비스키를 발급받으세요.
  2. [재난안전데이터공유플랫폼](https://www.safetydata.go.kr) 에서도 관련 사고 데이터를 확인할 수 있습니다.
  3. 위 `REGIONS`, `INCIDENTS` 리스트를 실제 데이터로 바꾸거나,
     사이드바의 `fetch_live_data()` 함수를 발급받은 서비스키로 연결해 사용하세요.
        """
    )
