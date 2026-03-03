# CiviSense: 시스템 아키텍처

## 1. 전체 구성도

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                   Frontend (Streamlit)                       │
                    │  민원 입력, 목록/상세, 통계 대시보드, Q&A                    │
                    └───────────────────────────┬─────────────────────────────────┘
                                                │ HTTP (REST) → Backend API
                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           Backend (FastAPI)                                        │
│  POST /complaints          GET /complaints         GET /complaints/:id/stats       │
│  GET /complaints/:id       POST /complaints/:id/qa  GET /dashboard/summary         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Complaint   │  │ Complaint   │  │ Dashboard   │  │ QnA Service             │  │
│  │ Service     │  │ Repository  │  │ Service     │  │ (요약 기반 답변)         │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  └────────────┬──────────────┘  │
│         │                │                 │                       │                │
│         │                ▼                 ▼                       │                │
│         │         ┌─────────────┐  ┌─────────────┐                │                │
│         │         │ DB (SQLite/  │  │ (같은 DB)   │                │                │
│         │         │  PostgreSQL) │  │             │                │                │
│         │         │  분류, 응답) │  │             │                │                │
│         │         └─────────────┘  └─────────────┘                │                │
│         │                                                          │                │
│         │  트리거 분석 파이프라인                                   │                │
│         ▼                                                          ▼                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                    Agent Pipeline (LangGraph)                                 │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐  │  │
│  │  │ Summarizer  │──▶│ Classifier  │──▶│ Urgency     │──▶│ Response        │  │  │  │
│  │  │ Node        │   │ Node        │   │ Detector    │   │ Generator Node  │  │  │  │
│  │  └─────────────┘   └─────────────┘   │ Node        │   │ (RAG 컨텍스트)  │  │  │  │
│  │        │                  │          └─────────────┘   └────────┬────────┘  │  │  │
│  │        │                  │                   │                     │         │  │  │
│  │        ▼                  ▼                   ▼                     ▼         │  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │  │
│  │  │                     Shared State (ComplaintState)                       │  │  │  │
│  │  │  raw_text, summary, complaint_type, urgency, response_draft, ...        │  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │  │
│         │                          │                                              │  │
│         │                          │ 유사 민원 검색                                │  │
│         ▼                          ▼                                              │  │
│  ┌─────────────┐           ┌─────────────┐                                        │  │
│  │ Upstage     │           │ ChromaDB    │                                        │  │
│  │ Solar API   │           │ (RAG)       │                                        │  │
│  └─────────────┘           └─────────────┘                                        │  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 컴포넌트 역할

### 2.1 Frontend (Streamlit)
- **민원 등록**: `st.text_area` 또는 `.txt` 파일 업로드 → Backend `POST /api/complaints` 호출.
- **목록**: 테이블/필터(유형, 긴급도, 상태, 기간) → `GET /api/complaints`.
- **상세**: 원문, 요약, 유형, 긴급도, 응답 초안 표시 + Q&A 입력 폼 → `GET /api/complaints/:id`, `POST /api/complaints/:id/qa`.
- **대시보드**: 유형별/긴급도별/상태별 건수 → `GET /api/dashboard/summary`.
- **실행**: `streamlit run app.py` (별도 포트, 예: 8501). Backend Base URL은 환경 변수.

### 2.2 Backend (FastAPI)
- **Complaint API**: 민원 접수(POST) → DB 저장 → Agent 파이프라인 비동기 호출 → 202 Accepted + complaint_id 반환.  
  (또는 동기: 파이프라인 완료 후 저장 후 201 + 결과 반환. 정책에 따라 선택.)
- **조회 API**: 목록(페이징, 필터), 상세(요약·분류·응답·긴급도).
- **Dashboard API**: 집계(유형별/긴급도별/상태별 건수).
- **QnA API**: `POST /complaints/:id/qa` — 해당 민원 요약 기반 질의응답.
- **에이전트 호출**: 내부 서비스에서 LangGraph `ainvoke` 호출, 결과를 DB에 반영.

### 2.3 Agent Pipeline (LangGraph)
- **입력**: 민원 원문(raw_text).
- **출력**: summary, complaint_type, urgency, response_draft.
- **노드 순서**: Summarizer → Classifier → UrgencyDetector → (RAG 검색) → ResponseGenerator.
- **상태**: 모든 노드가 공유 상태(ComplaintState)를 읽고 쓰며, 최종 상태를 Backend에 전달해 DB 저장.

### 2.4 RAG (ChromaDB)
- **인덱싱**: 기 저장된 민원의 요약+유형+응답 요약(또는 일부 본문)을 임베딩하여 저장.
- **검색 시점**: ResponseGenerator 노드 실행 전, 현재 요약·유형으로 유사 문서 top-k 검색.
- **사용**: 검색된 “유사 민원 + 응답”을 프롬프트 컨텍스트로 넣어 응답 초안 품질·일관성 향상.

### 2.5 DB (SQLite 기본 / PostgreSQL 선택)
- 민원 마스터, 요약, 유형, 긴급도, 응답 초안, 상태, 생성/수정 시각.
- 기본: SQLite(파일). 서비스화 시 PostgreSQL 등으로 `DATABASE_URL`만 변경.
- (선택) 기관, 담당자, 템플릿 설정 테이블 — 1차는 단일 테넌트 가정.

---

## 3. 데이터 흐름 (민원 1건 기준)

1. **사용자**: 프론트에서 민원 텍스트(또는 파일) 제출.
2. **Backend**: `POST /complaints` 수신 → 원문 DB 저장(상태: `pending` 또는 `processing`) → Agent 파이프라인 `ainvoke` 호출.
3. **Agent**:
   - Summarizer: 원문 → 구조화 요약 → State.summary.
   - Classifier: summary(+원문) → 유형 라벨 → State.complaint_type.
   - UrgencyDetector: summary(+원문) → urgency → State.urgency.
   - RAG: summary/type로 ChromaDB 검색 → 유사 사례 리스트.
   - ResponseGenerator: summary + type + urgency + 유사 사례 → 응답 초안 → State.response_draft.
4. **Backend**: 파이프라인 반환값으로 DB 업데이트(요약, 유형, 긴급도, 응답 초안, 상태: `completed`).  
   (실패 시 상태: `failed`, 에러 메시지 저장.)
5. **RAG 인덱싱**(백그라운드 또는 저장 시): 새 민원 요약+응답을 ChromaDB에 추가(다음 검색에 활용).
6. **사용자**: 목록/상세 화면에서 결과 조회, 필요 시 Q&A로 추가 질문.

---

## 4. 에러·재시도 정책

- **LLM 호출 실패**: 노드 내에서 1회 재시도, 실패 시 State에 error 플래그 + 메시지.
- **DB 저장 실패**: 트랜잭션 롤백, 클라이언트에 5xx 및 메시지 반환.
- **RAG 검색 실패**: ResponseGenerator는 RAG 없이 진행(폴백).

---

## 5. 보안·설정

- **API 키**: Upstage API Key, DB URL, ChromaDB 경로 등은 환경 변수(.env), 코드에 하드코딩 금지.
- **민원 데이터**: 개인정보 포함 가능하므로 접근 로그·보관 정책은 운영 규정에 따름.
- **CORS**: Streamlit(다른 포트)에서 API 호출 시 FastAPI CORS에 Streamlit 오리진 허용.

---

**문서 버전**: 1.0
