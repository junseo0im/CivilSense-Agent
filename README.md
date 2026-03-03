# CiviSense

멀티 에이전트(LangGraph) + RAG로 **민원 문서를 자동 분석하고 응답 초안을 생성하는 데모 프로젝트**입니다.

---

## ✨ 주요 기능

- **민원 요약**: 긴 민원 본문을 작성자 정보 / 사건 개요 / 요청 사항 등으로 구조화 요약
- **유형 분류**: 불편신고 / 문의 / 건의 / 진정 / 청구 / 기타 등의 민원 유형 자동 분류
- **긴급도 판단**: 키워드 규칙 + LLM 조합으로 긴급 / 보통 / 일반 판별
- **유사 민원 RAG**: 과거 민원·응답을 ChromaDB에 저장하고, 유사 사례를 검색해 응답에 반영
- **응답 초안 생성**: 요약·유형·긴급도·유사 사례를 반영한 정중한 응답 문 초안 생성
- **Q&A & 대시보드**: 요약 기반 Q&A, 유형·긴급도·상태별 통계를 Streamlit UI에서 확인

---

## 🛠️ 핵심 기술 스택

- **LLM**: Upstage Solar API (요약, 분류, 긴급도 판단, 응답 생성, Q&A)
- **에이전트 오케스트레이션**: LangGraph `StateGraph`  
  (Summarizer → Classifier → UrgencyDetector → RAG Search → ResponseGenerator)
- **RAG**: ChromaDB PersistentClient + 임베딩 API
- **백엔드**: FastAPI, SQLAlchemy (async), SQLite (데모용)
- **프론트엔드(UI)**: Streamlit (민원 입력, 목록/상세, Q&A, 대시보드)

- 아키텍처: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- PRD·API 명세·에이전트/RAG 설계 등: `docs/reference/`

---

## 🚀 빠른 시작

1. **환경 변수**  
   프로젝트 루트 또는 `backend/` 에 `.env` 생성 후 아래 설정.  
   - `UPSTAGE_API_KEY` (필수) — Upstage Solar API 키  
   - `UPSTAGE_BASE_URL` (선택) — 기본값 `https://api.upstage.ai/v1/solar`  
   - `DATABASE_URL` (선택) — 기본값 `sqlite+aiosqlite:///./civisense.db`

2. **Backend 실행** (터미널 1)
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. **Streamlit UI 실행** (터미널 2, **프로젝트 루트**에서 실행)
   ```bash
   pip install -r streamlit_app/requirements.txt
   streamlit run streamlit_app/app.py --server.port 8501
   ```

4. 브라우저에서 접속  
   - UI: `http://localhost:8501`  
   - API: `http://localhost:8000`

---

## 📄 라이선스

MIT

