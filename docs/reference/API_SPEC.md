# CiviSense: API 명세

## 1. 기본 사항

- **Base URL**: `http://localhost:8000` (또는 환경에 따라 변경).
- **인증**: 1차는 API Key 헤더 `X-API-Key` 또는 생략. 추후 JWT/세션 확장.
- **공통 응답**:
  - 성공: 2xx, JSON body.
  - 클라이언트 에러: 4xx, `{"detail": "..."}`.
  - 서버 에러: 5xx, `{"detail": "..."}`.

---

## 2. 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| POST | /api/complaints | 민원 접수 및 분석 트리거 |
| GET | /api/complaints | 민원 목록 (페이징·필터) |
| GET | /api/complaints/{id} | 민원 상세 |
| POST | /api/complaints/{id}/qa | 요약 기반 Q&A |
| GET | /api/dashboard/summary | 대시보드 통계 (유형별/긴급도별 건수) |
| GET | /health | 서버 상태 (선택) |

---

## 3. 상세 명세

### 3.1 POST /api/complaints

- **설명**: 민원 원문을 접수하고, 백엔드에서 LangGraph 파이프라인을 실행한 뒤 결과를 DB에 저장.
- **Request**
  - **Content-Type**: `application/json`.
  - **Body**:
    ```json
    {
      "raw_text": "민원 원문 전체 텍스트..."
    }
    ```
  - 또는 **Content-Type**: `multipart/form-data`, **file**: .txt 파일 (그 경우 파일 내용을 `raw_text`로 사용).
- **Response**
  - **202 Accepted** (비동기 처리 시):
    ```json
    {
      "complaint_id": 123,
      "status": "processing",
      "message": "민원이 접수되었습니다. 분석 완료 후 목록에서 확인하세요."
    }
    ```
  - **201 Created** (동기 처리 시 — 파이프라인 완료 후 저장 후 반환):
    ```json
    {
      "complaint_id": 123,
      "status": "completed",
      "summary": { ... },
      "complaint_type": "문의",
      "urgency": "normal",
      "response_draft": "안녕하세요. 귀하의 민원을 접수하였습니다..."
    }
    ```
- **에러**: 400 (raw_text 누락/빈 값), 500 (서버/파이프라인 오류).

---

### 3.2 GET /api/complaints

- **설명**: 민원 목록 조회. 쿼리 파라미터로 페이징·필터.
- **Query Parameters**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| page | int | 페이지 번호 (1부터), default 1 |
| page_size | int | 페이지당 건수, default 20 |
| status | string | pending / processing / completed / failed |
| complaint_type | string | 유형 필터 |
| urgency | string | urgent / normal / low |
| from_date | string (ISO date) | created_at >= from_date |
| to_date | string (ISO date) | created_at <= to_date |

- **Response 200**
  ```json
  {
    "items": [
      {
        "id": 123,
        "raw_text_preview": "민원 원문 앞 200자...",
        "summary": { ... },
        "complaint_type": "문의",
        "urgency": "normal",
        "status": "completed",
        "created_at": "2025-03-02T10:00:00Z"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
  ```

---

### 3.3 GET /api/complaints/{id}

- **설명**: 민원 1건 상세. 요약, 유형, 긴급도, 응답 초안, 원문, 상태 등.
- **Response 200**
  ```json
  {
    "id": 123,
    "raw_text": "전체 원문",
    "summary": {
      "작성자정보": "...",
      "사건개요": "...",
      "요청사항": "..."
    },
    "complaint_type": "문의",
    "complaint_type_confidence": 0.92,
    "urgency": "normal",
    "urgency_reason": "일반적인 문의 사항으로 판단됩니다.",
    "response_draft": "생성된 응답 초안 전문...",
    "status": "completed",
    "error_message": null,
    "created_at": "2025-03-02T10:00:00Z",
    "updated_at": "2025-03-02T10:01:30Z"
  }
  ```
- **404**: 해당 id 없음.

---

### 3.4 POST /api/complaints/{id}/qa

- **설명**: 해당 민원의 요약을 컨텍스트로 질의응답.
- **Request**
  ```json
  {
    "question": "요청하신 사항은 언제 처리되나요?"
  }
  ```
- **Response 200**
  ```json
  {
    "answer": "요약된 민원 내용에 따르면, 해당 사항은 ... 로 처리될 예정입니다."
  }
  ```
- **404**: 해당 민원 없음. **400**: question 누락.

---

### 3.5 GET /api/dashboard/summary

- **설명**: 대시보드용 집계. 유형별·긴급도별·상태별 건수.
- **Query Parameters**: (선택) `from_date`, `to_date`.
- **Response 200**
  ```json
  {
    "by_type": {
      "문의": 50,
      "불편신고": 20,
      "건의": 10
    },
    "by_urgency": {
      "urgent": 5,
      "normal": 60,
      "low": 15
    },
    "by_status": {
      "completed": 70,
      "processing": 2,
      "pending": 5,
      "failed": 3
    },
    "total": 80
  }
  ```
  - 기간 필터 시 해당 기간 내 건수만 집계.

---

### 3.6 GET /health

- **설명**: 서버·DB 연결 상태 확인.
- **Response 200**: `{"status": "ok", "db": "connected"}` 등.

---

## 4. 구현 시 참고

- **동기 vs 비동기**: PRD/아키텍처에 따라 1차는 **동기**(파이프라인 완료 후 201 반환)로 구현해도 됨. 대기 시간이 길어지면 202 + 폴링(목록/상세에서 status 확인)으로 전환.
- **파일 업로드**: `POST /api/complaints`에서 `multipart/form-data` + `file` 수신 시, 파일 내용을 읽어 `raw_text`로 넘기면 됨.

---

**문서 버전**: 1.0
