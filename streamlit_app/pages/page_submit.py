import streamlit as st
from api_client import post_complaint


def render():
    st.title("민원 접수")
    st.caption("민원 원문을 입력하거나 .txt 파일을 업로드한 뒤 분석을 요청하세요.")

    with st.container():
        raw = st.text_area(
            "민원 내용",
            height=200,
            placeholder="민원 원문을 붙여넣거나 아래에서 .txt 파일을 업로드하세요.",
            label_visibility="collapsed",
        )
        file = st.file_uploader(".txt 파일 업로드", type=["txt"], label_visibility="visible")
        if file:
            raw = file.read().decode("utf-8", errors="replace")
            st.text_area("파일 내용", value=raw, height=200, disabled=True, key="loaded")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        submit = st.button("분석 요청", type="primary", use_container_width=True)

    if submit:
        text = (raw or "").strip()
        if not text:
            st.error("민원 내용을 입력하거나 파일을 업로드해 주세요.")
            return
        with st.spinner("요약 → 유형 분류 → 긴급도 판단 → 응답 초안 생성 중..."):
            try:
                result = post_complaint(text)
                st.success("분석이 완료되었습니다.")

                a, b, c = st.columns(3)
                with a:
                    st.metric("민원 유형", result.get("complaint_type") or "-")
                with b:
                    st.metric("긴급도", result.get("urgency") or "-")
                with c:
                    st.metric("상태", result.get("status") or "-")

                with st.expander("요약 보기", expanded=True):
                    summary = result.get("summary") or {}
                    if isinstance(summary, dict):
                        for k, v in (summary or {}).items():
                            st.markdown(f"**{k}**")
                            st.write(v if v else "-")
                    else:
                        st.write(summary)

                with st.expander("응답 초안", expanded=True):
                    st.text_area(
                        "",
                        value=result.get("response_draft") or "",
                        height=280,
                        disabled=True,
                        key="draft_result",
                        label_visibility="collapsed",
                    )

                if result.get("error_message"):
                    st.warning("참고: " + result["error_message"])
            except Exception as e:
                err_msg = str(e)
                if hasattr(e, "response"):
                    try:
                        body = e.response.json()
                        if isinstance(body.get("detail"), str):
                            err_msg = body["detail"]
                    except Exception:
                        pass
                st.error("요청 실패: " + err_msg)
