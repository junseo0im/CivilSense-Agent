# SmartForm-Agent: 데이터 모델 (DB 스키마)

## 1. 개요

- **DBMS**: PostgreSQL.
- **ORM**: SQLAlchemy 2.0 (async). 마이그레이션: Alembic.
- **1차 버전**: 단일 테넌트(기관 구분 없음). 필요 시 `organization_id` 등 확장.

---

## 2. ER 개요

```
complaints (민원 마스터)
    │
    ├── 1:1 summary, type, urgency, response (같은 테이블 컬럼 또는 별도 테이블)
    │
    └── (선택) complaint_qa (Q&A 대화 기록)
```

- 1차는 **단일 테이블 `complaints`** 로 모든 필드 저장. 정규화는 추후 필요 시 분리.

---

## 3. 테이블 정의

### 3.1 complaints

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| id | BIGSERIAL | PK | 민원 ID |
| raw_text | TEXT | NOT NULL | 민원 원문 |
| summary | JSONB | NULL | 구조화 요약 (작성자, 개요, 요청사항 등) |
| complaint_type | VARCHAR(100) | NULL | 유형 (불편신고, 문의, 건의 등) |
| complaint_type_confidence | REAL | NULL | 분류 신뢰도 0~1 |
| urgency | VARCHAR(20) | NULL | urgent / normal / low |
| urgency_reason | TEXT | NULL | 긴급도 판단 근거 |
| response_draft | TEXT | NULL | 생성된 응답 초안 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending / processing / completed / failed |
| error_message | TEXT | NULL | 파이프라인 실패 시 에러 메시지 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 접수 시각 |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 최종 수정 시각 |

- **인덱스**: `created_at`, `status`, `complaint_type`, `urgency` (목록/대시보드 필터용).

### 3.2 complaint_qa 

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| id | BIGSERIAL | PK | Q&A 기록 ID |
| complaint_id | BIGINT | FK(complaints.id), NOT NULL | 민원 ID |
| question | TEXT | NOT NULL | 사용자 질문 |
| answer | TEXT | NOT NULL | 시스템 생성 답변 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 생성 시각 |

- **인덱스**: `complaint_id`.

---

## 4. SQLAlchemy 모델 예시

```python
from sqlalchemy import String, Text, Float, BigInteger, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    complaint_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complaint_type_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    urgency_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

- `status` 값: `pending`, `processing`, `completed`, `failed`.

---

## 5. ChromaDB (RAG)

- **컬렉션**: `complaint_cases`.
- **저장 필드**:
  - `id`: 문서 ID (예: `complaint_{complaint_id}`).
  - `embedding`: 벡터.
  - `document`: 검색용 텍스트 (요약 + 유형 + 응답 스니펫).
  - `metadata`: `complaint_id`, `complaint_type`, `urgency`, `created_at`, `response_snippet` (선택).

---

**문서 버전**: 1.0
