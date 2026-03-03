import streamlit as st

st.set_page_config(
    page_title="CiviSense",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("CiviSense")
st.sidebar.caption("민원 자동 분석 · 응답 초안 생성")
st.sidebar.divider()
page = st.sidebar.radio(
    "메뉴",
    ["📥 민원 접수", "📋 민원 목록", "🔍 상세 / Q&A", "📊 대시보드"],
    index=0,
    label_visibility="collapsed",
)

if "민원 접수" in page:
    from pages import page_submit
    page_submit.render()
elif "민원 목록" in page:
    from pages import page_list
    page_list.render()
elif "상세" in page or "Q&A" in page:
    from pages import page_detail_qa
    page_detail_qa.render()
else:
    from pages import page_dashboard
    page_dashboard.render()
