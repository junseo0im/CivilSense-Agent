# CiviSense: 에이전트 설계 (LangGraph)

## 1. 개요

민원 1건당 **단일 파이프라인**으로 다음을 순차 수행한다.

1. **요약** (Summarizer)
2. **유형 분류** (Classifier)
3. **긴급도 판단** (UrgencyDetector)
4. **유사 민원 검색** (RAG — ResponseGenerator 직전)
5. **응답 문 생성** (ResponseGenerator)

모든 노드는 **공유 상태(ComplaintState)**를 읽고 쓰며, Backend는 최종 State를 DB에 반영한다.

---

## 2. 상태 정의 (ComplaintState)

| 필드 | 타입 | 설명 | 설정 주체 |
|------|------|------|-----------|
| `complaint_id` | str (optional) | DB 상의 민원 ID (Backend에서 주입) | Backend |
| `raw_text` | str | 민원 원문 | Backend |
| `summary` | dict / str | 구조화 요약 (작성자, 개요, 요청사항 등) | Summarizer |
| `complaint_type` | str / list | 유형 라벨(단일 또는 다중) | Classifier |
| `complaint_type_confidence` | float (optional) | 분류 신뢰도 | Classifier |
| `urgency` | str | `urgent` / `normal` / `low` | UrgencyDetector |
| `urgency_reason` | str (optional) | 긴급도 판단 근거 | UrgencyDetector |
| `rag_context` | list[dict] | RAG 검색 결과 (유사 민원 요약·응답) | RAG 검색 |
| `response_draft` | str | 생성된 응답 초안 | ResponseGenerator |
| `error` | str (optional) | 파이프라인 내 에러 메시지 | 어느 노드든 |
| `current_step` | str | 디버깅용 현재 단계명 | 각 노드 |

**TypedDict 예시 (Python):**

```python
from typing import TypedDict, Optional, List

class ComplaintState(TypedDict):
    complaint_id: Optional[str]
    raw_text: str
    summary: Optional[dict]
    complaint_type: Optional[str]
    complaint_type_confidence: Optional[float]
    urgency: Optional[str]
    urgency_reason: Optional[str]
    rag_context: Optional[List[dict]]
    response_draft: Optional[str]
    error: Optional[str]
    current_step: Optional[str]
```

---

## 3. 노드 상세

### 3.1 Summarizer Node

- **입력**: `raw_text`
- **출력**: `summary`, `current_step = "summarized"`
- **로직**:
  - Upstage Solar API 호출 (요약 전용 프롬프트).
  - 프롬프트 지시: "민원 문서를 다음 항목으로 구조화하여 JSON으로 출력: 작성자정보, 사건개요, 요청사항, 기타."
  - 응답을 파싱해 `summary`에 dict 또는 JSON 문자열로 저장.
- **에러**: 파싱 실패 시 `summary`에 원문 일부 요약 또는 빈 구조, `error`에 메시지.

### 3.2 Classifier Node

- **입력**: `raw_text`, `summary`
- **출력**: `complaint_type`, `complaint_type_confidence`, `current_step = "classified"`
- **로직**:
  - Upstage Solar API 호출 (분류 전용 프롬프트).
  - 사전 정의 유형 예: 불편신고, 문의, 건의, 진정, 청구, 기타. (유형 목록은 설정 가능)
  - 출력: `{"type": "...", "confidence": 0.9}` 형태로 파싱.
- **에러**: 실패 시 `complaint_type = "기타"`, `confidence = 0.0`.

### 3.3 UrgencyDetector Node

- **입력**: `raw_text`, `summary`
- **출력**: `urgency`, `urgency_reason`, `current_step = "urgency_done"`
- **로직**:
  - 키워드 규칙(파손, 사고, 위험, 긴급 등) + Upstage Solar API 호출로 이중 판단.
  - 규칙으로 긴급 후보 추출 → LLM으로 "긴급/보통/일반" 중 선택 및 짧은 근거 문장 생성.
  - `urgency`: `urgent` | `normal` | `low`.
- **에러**: 실패 시 `urgency = "normal"`, `urgency_reason = "자동 판단 실패"`.

### 3.4 RAG 검색 (ResponseGenerator 직전)

- **입력**: `summary`, `complaint_type`
- **출력**: `rag_context` (list of { "summary", "response_snippet", "similarity" } 등)
- **로직**:
  - 요약 텍스트(또는 summary + type 문자열)를 임베딩.
  - ChromaDB에서 top-k (예: 3~5) 유사 문서 검색.
  - 메타데이터에서 응답 요약 또는 스니펫 첨부.
  - ResponseGenerator 노드에서 이 리스트를 컨텍스트로 사용.

### 3.5 ResponseGenerator Node

- **입력**: `summary`, `complaint_type`, `urgency`, `rag_context`
- **출력**: `response_draft`, `current_step = "response_generated"`
- **로직**:
  - Upstage Solar API 호출.
  - 프롬프트: "다음 민원 요약과 유형·긴급도를 반영하여, 정중한 공식 응답 문 초안을 작성하라. 아래 유사 사례를 참고할 수 있다." + `rag_context` 요약.
  - 출력을 그대로 `response_draft`에 저장.
- **에러**: 실패 시 `response_draft = ""`, `error`에 메시지.

---

## 4. 그래프 정의 (LangGraph)

- **노드**: `summarizer`, `classifier`, `urgency_detector`, `response_generator`.
- **엣지** (순차):
  - START → summarizer
  - summarizer → classifier
  - classifier → urgency_detector
  - urgency_detector → (RAG 검색 로직 — 별도 함수 또는 response_generator 내부 1단계)
  - (RAG 후) → response_generator
  - response_generator → END
- **RAG**는 response_generator 노드 **진입 시** 같은 State를 사용해 검색한 뒤, State에 `rag_context`를 채우고 본문 생성으로 진행하거나, "RAG 검색 전용 노드"를 하나 두고 `urgency_detector → rag_search → response_generator` 로 연결해도 됨. (문서 상으로는 "ResponseGenerator 직전"에 RAG 수행으로 정의.)

**권장**: `rag_search` 노드를 명시적으로 두고, `urgency_detector → rag_search → response_generator` 로 구성하면 상태 추적과 테스트가 쉬움.

---

## 5. Backend 연동

- Backend는 민원 접수 시:
  1. `ComplaintState` 초기값: `raw_text`, (선택) `complaint_id`.
  2. `workflow.ainvoke(initial_state)` 호출.
  3. 반환된 State에서 `summary`, `complaint_type`, `urgency`, `response_draft` 등을 읽어 DB 업데이트.
  4. 실패 시 `error`, `current_step` 저장하여 디버깅 및 상태 `failed` 처리.

---

## 6. Q&A (요약 기반)

- Q&A는 **별도 API**로 처리: `POST /complaints/:id/qa` 에 `{"question": "..."}` 전달.
- Backend에서 해당 민원의 `summary`(및 필요 시 원문 일부)를 컨텍스트로 Upstage Solar API 호출 → 답변 텍스트 반환.
- LangGraph 파이프라인에 "Q&A 노드"를 넣을 필요는 없고, 기존 요약을 활용하는 **단일 LLM 호출**로 충분.

---

**문서 버전**: 1.0
