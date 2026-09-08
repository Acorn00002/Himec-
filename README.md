# Engineering CrossCheck Agent

전기·기계 설비 설계 문서(사양서, 도면, 계산서, Equipment List 등)를 AI가 분석해
**동일 설비(TAG)에 대한 정보가 문서마다 일치하는지 자동으로 검증**하는 Engineering Review Assistant.

> "설계자는 설계하고, AI는 설계를 검증한다."

이 시스템은 설계를 승인하지 않습니다. AI 검토 결과이며 최종 설계 판단은 담당 엔지니어의 확인이 필요합니다.

## 핵심 기능
- PDF/이미지/Excel/CSV/TXT에서 문서를 실제로 파싱(pdfplumber/openpyxl)하고, Gemini로 설비 TAG와 사양 데이터를 추출
- 동일 TAG의 데이터를 문서 간 Cross-check (값/단위/누락/이상값) — 비교 자체는 deterministic 코드
- 불일치의 심각도(INFO/LOW/MEDIUM/HIGH)는 규칙 기반으로 결정하고, AI는 그 판단의 근거를 설명하는 역할만 수행
- 오류가 다른 설계 항목(케이블/차단기/배전반 등)에 미치는 영향 분석(Impact Analysis)
- 프로젝트 리포트를 PDF로 Export (Executive Summary + 근거/영향 포함 상세 Findings)
- 근거 문서/페이지·Sheet 위치를 모든 이슈에 함께 표시

## 구조
```
backend/   FastAPI + SQLAlchemy + SQLite (dev)
           services/parsing/   PDF·XLSX·CSV·TXT deterministic 파서 (Phase 8)
           services/ai/        Gemini 추출·추론 (Phase 9), 계산/판단은 하지 않음
           services/crosscheck_basic.py  단위 변환 포함 값 비교 (deterministic)
           services/issue_rules.py       심각도/영향 항목 규칙 (deterministic)
           services/crosscheck_engine.py 위 둘을 묶어 실제 업로드 프로젝트의 Issue 생성
           services/report.py            PDF 리포트 생성
frontend/  Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts
```

## 시작하기

### 환경 변수
루트의 `.env.example`을 `.env`로 복사하고 `GEMINI_API_KEY`를 채워주세요
([https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)에서 발급).
키가 없어도 앱 전체(파싱 포함)는 정상 동작하며, AI 추출/추론 단계만 자동으로 건너뛰고
deterministic fallback을 사용합니다 — Demo Project는 API 키 없이 항상 완전히 동작합니다.

### Backend
```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt
./venv/Scripts/uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

프론트엔드는 http://localhost:3000, 백엔드는 http://localhost:8000 에서 실행됩니다.
(3000번 포트가 이미 사용 중이면 `npm run dev -- -p 3100`처럼 다른 포트를 쓰고, 백엔드 `CORS_ORIGINS`에도 추가하세요.)

랜딩 페이지에서 **Load Demo Project**를 누르면 의도적으로 오류가 섞인 데모 설계 데이터셋이 즉시 로드됩니다.
**New Project**로 시작하면 실제 문서를 업로드해 Phase 8~12 파이프라인(파싱 → AI 추출 → CrossCheck → 리포트)을 그대로 체험할 수 있습니다.

### 테스트
```bash
cd backend
./venv/Scripts/pytest -q
```
`GEMINI_API_KEY`가 설정되어 있으면 실제 Gemini 호출을 포함한 `test_ai_pipeline.py`도 함께 실행됩니다.

## 개발 현황
Phase 1~12 전체가 구현되어 있습니다: 프로젝트 구조/Demo Dataset/Dashboard/Equipment Explorer/CrossCheck Table/
Issue Detail/Document Upload UI(Phase 1~7), 실제 PDF·XLSX·CSV·TXT 파싱(Phase 8), Gemini 기반 TAG/사양 추출(Phase 9),
CrossCheck 엔진 + 규칙 기반 심각도·Impact Analysis(Phase 10~11), PDF 리포트 생성(Phase 12).
이미지(나메플레이트 사진 등)는 Gemini vision으로 직접 처리하며, CAD 등 추가 포맷은 같은 `services/parsing/` 구조에
파서를 추가하는 방식으로 확장 가능하도록 설계되어 있습니다.
