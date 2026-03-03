import streamlit as st
from api_client import get_complaints

STATUS_LABELS = {"": "전체", "pending": "대기", "processing": "처리중", "completed": "완료", "failed": "실패"}
URGENCY_LABELS = {"": "전체", "urgent": "긴급", "normal": "보통", "low": "낮음"}
TYPE_OPTIONS = ["", "문의", "불편신고", "건의", "진정", "청구", "기타"]


def render():
    st.title("민원 목록")
    st.caption("필터를 선택한 뒤 목록을 확인하고, 상세는 '상세 / Q&A' 메뉴에서 ID로 조회할 수 있습니다.")

    col1, col2, col3 = st.columns(3)
    with col1:
        status = st.selectbox(
            "상태",
            list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS[x],
        )
    with col2:
        complaint_type = st.selectbox(
            "유형",
            TYPE_OPTIONS,
            format_func=lambda x: x or "전체",
        )
    with col3:
        urgency = st.selectbox(
            "긴급도",
            list(URGENCY_LABELS.keys()),
            format_func=lambda x: URGENCY_LABELS[x],
        )

    try:
        data = get_complaints(
            page=1,
            page_size=50,
            status=status or None,
            complaint_type=complaint_type or None,
            urgency=urgency or None,
        )
    except Exception as e:
        st.error("목록 조회 실패: " + str(e))
        return

    items = data.get("items", [])
    total = data.get("total", 0)
    st.metric("조회 결과", f"{total}건")

    if not items:
        st.info("조건에 맞는 민원이 없습니다.")
        return

    for row in items:
        rid = row["id"]
        ctype = row.get("complaint_type") or "-"
        urg = row.get("urgency") or "-"
        status_val = row.get("status") or "-"
        urg_label = URGENCY_LABELS.get(urg, urg)
        status_label = STATUS_LABELS.get(status_val, status_val)
        preview = (row.get("raw_text_preview") or "")[:200]
        created = row.get("created_at") or ""

        with st.expander(f"#{rid} · {ctype} · {urg_label} · {status_label}"):
            st.caption(f"작성일: {created}")
            st.write(preview + ("…" if len((row.get("raw_text_preview") or "")) > 200 else ""))
            st.caption(f"상세 보기: '상세 / Q&A' 메뉴에서 ID **{rid}** 입력 후 조회")
