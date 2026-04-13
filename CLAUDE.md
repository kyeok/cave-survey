# cave-survey

CAVE 연구 설문 웹앱. **"AI가 관리 기능을 자동화하면 조직은 더 자율적으로 되는가"** 질문을 42문항으로 측정. AI Ops Pattern(P0~P4) 산출.

## 스택
- **Backend**: FastAPI
- **Template**: Jinja2
- **Auth**: Google OAuth
- **Storage**: Google Sheets
- **배포**: Railway (`https://daolab7-cave.up.railway.app`)

## 3축 구조 (절대 변경 금지 — 연구 설계와 묶여 있음)
| 축 | 측정 대상 |
|---|---|
| Context Engineering | 맥락 구성 활동 (일정·추적·기록·공지·지식·분석) |
| Core Work | 본업 수행 활동 (산출물·검증·우선순위) |
| Agency Direction | 구성원 자발 / 리더 권장 / 조직 시스템 |

## 설문 구조 (42문항, 17분)
- Part A-1 (6) · A-2 (3) · B (8) · C (12) · D (10) · E (3 주관식)

## 주요 경로
- `main.py` · `templates/` · `docs/` · `Procfile` · `railway.json`

## 개발 루틴
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 주의
- **3축 정의·문항 수는 DAOLAB 7기 연구 설계 산출물**. 코드만 보고 리팩터하지 말 것 — 연구 설계 문서 확인 필수
- CAVE 조 5명의 L0~L4 역할(연구자·수집자·분석자 등) 기반 프로젝트. 데이터 관리 권한 조심
- Railway 환경변수는 콘솔에서만 관리 (`.env`는 로컬 전용)
- 응답 raw 데이터에 자유기술 포함 → 절대 commit 금지
