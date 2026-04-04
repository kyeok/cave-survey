# CAVE Survey — AI Ops Pattern 진단

> AI가 관리 기능을 자동화하면, 조직은 더 자율적으로 되는가?

42문항 설문으로 조직의 AI Ops Pattern(P0~P4)을 진단하는 웹앱입니다.

**Live**: https://daolab7-cave.up.railway.app

## 3축 측정 구조

| 축 | 설명 | 측정 |
|---|------|------|
| **Context Engineering** | AI로 맥락을 구성하는 활동 (일정·추적·기록·공지·지식·분석) | Part A-1 (6문항) |
| **Core Work** | AI로 본업을 수행하는 활동 (산출물·검증·우선순위) | Part A-2 (3문항) |
| **Agency Direction** | 누가 AI 활용을 주도하는가 (구성원 자발 / 리더 권장 / 조직 시스템) | Part A sub-Q |

## 설문 구조 (42문항, ~17분)

| Part | 문항 | 측정 |
|------|:---:|------|
| A-1 | 6 | CE Pattern (P0~P4) + 주체 방향 |
| A-2 | 3 | CW Pattern (P0~P4) + 주체 방향 |
| B | 8 | AI 활용 행동 패턴 (CE 4 + CW 4) |
| C | 12 | 자율성 기준선 9 + AI 기여 자율성 3 |
| D | 10 | 투명성 3 + AI 인식 2 + 감시 체감 3 + 위임 전환 2 |
| E | 3 | 주관식 (에피소드 + 리더 변화 + 조건 분기) |

## 결과 산출

- **AI Ops Pattern**: CE/CW 별도 + 종합 (P0~P4)
- **Agency Direction**: 자발 주도형 / 혼합형 / 시스템 주도형
- **자율성**: 기준선(C1\~C9) vs AI 기여(C10\~C12) 분리
- **투명성 vs 감시**: 정보 투명성 ↔ 감시 체감(가시성·평가 우려·행동 위축)
- **레이더 차트**: 9영역 Pattern + 6축 종합 프로필
- **PDF 다운로드**: 결과 + 질문별 응답 상세 포함

## 기술 스택

- **Backend**: FastAPI + Jinja2
- **Chart**: Chart.js (레이더 차트)
- **PDF**: html2canvas + jsPDF (클라이언트 사이드)
- **Auth**: Google OAuth 2.0
- **DB**: Google Sheets API
- **Deploy**: Railway

## 로컬 실행

```bash
pip install -r requirements.txt
DEV_MODE=true python main.py
# → http://localhost:8000
```

`DEV_MODE=true`로 OAuth 없이 테스트 가능합니다.

## 파일 구조

```
cave-survey/
├── main.py                          # FastAPI 서버 + 42문항 정의 + 결과 산출
├── templates/
│   ├── index.html                   # 메인 (데모 애니메이션)
│   ├── survey.html                  # 설문 (1문항 1화면)
│   ├── result.html                  # 결과 (레이더 차트 + PDF)
│   ├── guide.html                   # AI Ops Pattern 가이드
│   └── coverage.html                # 커버리지 맵
├── docs/
│   ├── cave-survey-phase1-before.md # 설문지 원본 (42문항)
│   ├── ai-ops-coverage-map.html     # 커버리지 맵 원본
│   └── persona-responses.md         # 10개 페르소나 가상 응답
├── requirements.txt
├── railway.json
└── Procfile
```

## CAVE 연구

다오랩 7기 4조 — Collective AI Ventures and Experiments

**연구 질문**: AI Ops는 자율조직을 강화하는가?

**핵심 가설**: 리더가 AI를 통해 정보를 더 투명하게 제공할수록, 구성원의 자율성은 높아진다. 단, 주체 방향(Bottom-up vs Top-down)이 이 관계를 조절한다.
