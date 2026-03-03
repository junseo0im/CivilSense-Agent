# CiviSense: RAG 설계

## 1. 목적

- **유사 과거 민원** 및 **그에 대한 처리/응답**을 검색해, **ResponseGenerator** 노드에서 참고하도록 함.
- 동일 기관·유형에서 사용했던 톤·처리 방식을 반영하여 **응답 품질·일관성**을 높인다.

---

## 2. 저장 대상 (ChromaDB)

### 2.1 문서 단위

- **한 건의 문서** = 과거 민원 1건에 대한 “검색용 텍스트” 1개.
- **검색용 텍스트** = 민원 요약(summary) + 유형(complaint_type) + (선택) 응답 요약 또는 응답 본문 앞 500자.
- **메타데이터** (ChromaDB metadata): `complaint_id`, `complaint_type`, `urgency`, `created_at`, (선택) `response_snippet`.

### 2.2 컬렉션

- **이름**: `complaint_cases` (또는 `civisense_complaints`).
- **임베딩 차원**: 사용하는 Embedding API에 따름 (Upstage/Voyage 등, 예: 512 또는 1024).
- **거리 메트릭**: 코사인 유사도 또는 내적(임베딩이 정규화된 경우).

---

## 3. 인덱싱 시점

- **민원 처리 완료 후**: Backend에서 파이프라인 결과를 DB에 저장한 뒤, **동일 트랜잭션 또는 백그라운드 태스크**에서 ChromaDB에 추가.
- **인덱싱 내용**: 해당 민원의 `summary`(문자열로 직렬화) + `complaint_type` + `response_draft`(앞 N자)를 합친 텍스트를 임베딩하고, `complaint_id` 등 메타데이터와 함께 upsert.

---

## 4. 검색 시점 및 방식

- **시점**: ResponseGenerator 노드 **실행 직전** (또는 전용 `rag_search` 노드에서).
- **쿼리**: 현재 민원의 `summary`(문자열) + `complaint_type`을 이어 붙인 텍스트를 임베딩.
- **검색**: ChromaDB에서 위 쿼리 벡터로 **top-k** (권장 3~5) 검색.
- **결과**: `rag_context` 리스트로 State에 저장. 각 항목: `summary`, `response_snippet`, `complaint_type`, (선택) `complaint_id`.
- ResponseGenerator 프롬프트에는 "아래 유사 사례를 참고하여 응답을 작성하라" + `rag_context` 요약을 포함.

---

## 5. 임베딩·벡터 DB

- **임베딩 모델**: Upstage Embedding API 또는 Voyage AI (프로젝트 정책에 따라 선택).
- **ChromaDB**: Persistent Client, 로컬 디렉터리 지정 (예: `./chroma_complaints`).
- **버전/캐시**: 인덱싱 로직 변경 시 기존 컬렉션 재구성 또는 버저닝 정책은 운영 요구에 따라 결정. (1차는 단순 upsert.)

---

## 6. 폴백

- **ChromaDB 장애/미설정**: RAG 검색 스킵, `rag_context = []`로 ResponseGenerator 실행. (요약+유형만으로 응답 생성.)
- **검색 결과 0건**: 동일.

---

## 7. 보안·개인정보

- RAG에 저장하는 텍스트에 **개인정보**가 포함되지 않도록, 요약 단계에서 개인정보 마스킹 정책을 적용할 수 있음. (1차는 요약본만 저장하고, 원문은 저장하지 않음.)

---

**문서 버전**: 1.0
