import streamlit as st
from api_client import get_dashboard_summary


def render():
    st.title("대시보드")
    st.caption("민원 유형·긴급도·처리 상태별 통계입니다.")

    try:
        data = get_dashboard_summary()
    except Exception as e:
        st.error("통계 조회 실패: " + str(e))
        return

    total = data.get("total", 0)
    st.metric("총 민원 건수", total)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("유형별")
        by_type = data.get("by_type") or {}
        if by_type:
            for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
                st.write(f"**{t}** · {cnt}건")
        else:
            st.caption("데이터 없음")
    with col2:
        st.subheader("긴급도별")
        by_urgency = data.get("by_urgency") or {}
        if by_urgency:
            for u, cnt in sorted(by_urgency.items(), key=lambda x: -x[1]):
                st.write(f"**{u}** · {cnt}건")
        else:
            st.caption("데이터 없음")
    with col3:
        st.subheader("상태별")
        by_status = data.get("by_status") or {}
        if by_status:
            for s, cnt in sorted(by_status.items(), key=lambda x: -x[1]):
                st.write(f"**{s}** · {cnt}건")
        else:
            st.caption("데이터 없음")
