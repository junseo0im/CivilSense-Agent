import streamlit as st
from api_client import get_complaint, post_qa, post_rating


def render():
    st.title("민원 상세 / Q&A")
    st.caption("민원 ID를 입력해 상세 내용을 보고, 요약 기반 질의응답과 응답 품질 평가를 할 수 있습니다.")

    cid = st.number_input(
        "민원 ID",
        min_value=1,
        value=st.session_state.get("detail_id", 1),
        key="detail_id",
        help="목록에서 확인한 ID를 입력하세요.",
    )
    if st.button("조회", type="primary"):
        try:
            c = get_complaint(int(cid))
            st.session_state["complaint_detail"] = c
        except Exception as e:
            st.error("조회 실패: " + str(e))
            return

    if "complaint_detail" not in st.session_state:
        st.info("민원 ID를 입력한 뒤 [조회]를 눌러 주세요.")
        return

    c = st.session_state["complaint_detail"]

    tab1, tab2, tab3 = st.tabs(["상세 정보", "요약 Q&A", "응답 평가"])

    with tab1:
        st.subheader("원문")
        st.text_area("", value=c.get("raw_text") or "", height=120, disabled=True, key="raw", label_visibility="collapsed")
        st.subheader("요약")
        summary = c.get("summary") or {}
        if isinstance(summary, dict):
            for k, v in summary.items():
                st.markdown(f"**{k}**")
                st.write(v if v else "-")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("유형", c.get("complaint_type") or "-")
        with col2:
            st.metric("긴급도", c.get("urgency") or "-")
        st.subheader("응답 초안")
        st.text_area("", value=c.get("response_draft") or "", height=220, disabled=True, key="draft", label_visibility="collapsed")

    with tab2:
        q = st.text_input("요약 내용을 바탕으로 질문을 입력하세요")
        if st.button("답변 생성") and (q or "").strip():
            try:
                r = post_qa(int(cid), q.strip())
                st.write("**답변**")
                st.write(r.get("answer", ""))
            except Exception as e:
                st.error("Q&A 실패: " + str(e))

    with tab3:
        existing_rating = c.get("response_rating")
        existing_feedback = c.get("response_feedback") or ""
        rating = st.slider(
            "응답 만족도 (1: 불만족 ~ 5: 매우 만족)",
            min_value=1,
            max_value=5,
            value=int(existing_rating) if isinstance(existing_rating, int) and 1 <= existing_rating <= 5 else 4,
        )
        feedback = st.text_area("추가 피드백 (선택)", value=existing_feedback, height=80)
        if st.button("평가 저장"):
            try:
                res = post_rating(int(cid), rating, feedback)
                st.success("평가가 저장되었습니다.")
                c["response_rating"] = res.get("response_rating")
                c["response_feedback"] = res.get("response_feedback")
                st.session_state["complaint_detail"] = c
            except Exception as e:
                st.error("평가 저장 실패: " + str(e))
