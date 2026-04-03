"""CAVE Survey — AI Ops Pattern 진단 웹앱 (42문항, 3축 구조)"""
import os
import json
from datetime import datetime, timezone, timedelta
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# ── Config ──
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "cave-survey-secret-key-change-me")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "1jxkDbA3We5z8gyot41P0P9eqvLL5xAvlSCi-sujXbsY")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

KST = timezone(timedelta(hours=9))

# ── App ──
app = FastAPI(title="CAVE Survey")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=BASE_URL.startswith("https"),
)
templates = Jinja2Templates(directory="templates")

# ── OAuth URLs ──
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

MEMBER_MAP = {"김계옥": "할리", "harley": "할리"}

# ── Pattern 정의 ──
PATTERN_NAMES = {0: "No AI", 1: "AI 보조", 2: "AI 협업", 3: "AI 위임", 4: "AI 자율"}


def pattern_level(avg):
    if avg < 0.5:
        return 0
    elif avg < 1.5:
        return 1
    elif avg < 2.5:
        return 2
    elif avg < 3.5:
        return 3
    else:
        return 4


# ── 설문 문항 정의 (42문항) ──
PATTERN_OPTIONS = [
    {"value": "na", "label": "N/A", "desc": "이 활동은 내 역할에 해당하지 않는다"},
    {"value": "0", "label": "P0", "desc": "AI 미사용. 사람이 직접 수행한다"},
    {"value": "1", "label": "P1", "desc": "AI 보조. AI가 정보를 제공하지만, 최종 판단은 사람이"},
    {"value": "2", "label": "P2", "desc": "AI 협업. AI가 초안을 만들고, 사람이 검토·수정"},
    {"value": "3", "label": "P3", "desc": "AI 위임. AI가 자율 실행, 사람은 예외만 처리"},
    {"value": "4", "label": "P4", "desc": "AI 자율. AI가 독립 운영, 사람은 목표만 설정"},
]

AGENCY_MEMBER = [
    {"value": "a", "label": "내가 스스로 선택하여 사용"},
    {"value": "b", "label": "리더/관리자가 권장하여 사용"},
    {"value": "c", "label": "조직 차원에서 시스템으로 도입"},
]

AGENCY_LEADER = [
    {"value": "a", "label": "내가 개인적으로 선택하여 사용"},
    {"value": "b", "label": "내가 리더로서 팀에 도입을 주도"},
    {"value": "c", "label": "상위 조직/전사 차원에서 시스템으로 도입"},
]

QUESTIONS = [
    # Part A-1: Context Engineering (6문항)
    {"id": "A1", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "일정 관리", "sub": "회의·마감·스프린트 계획", "color": "#ffd54f"},
    {"id": "A2", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "업무 추적", "sub": "진행 상황 파악·보고·현황 공유", "color": "#ffd54f"},
    {"id": "A3", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "회의록·기록", "sub": "회의 기록·지식 정리·문서화", "color": "#ffd54f"},
    {"id": "A4", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "공지·커뮤니케이션", "sub": "팀 공지·정보 공유", "color": "#ffd54f"},
    {"id": "A5", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "지식 관리", "sub": "기술 문서·위키·검색·온보딩 자료", "color": "#ffd54f"},
    {"id": "A6", "part": "A-1", "section": "Context Engineering", "type": "pattern",
     "text": "데이터 수집·분석", "sub": "지표 해석·트렌드 탐지·의사결정 지원", "color": "#ffd54f"},
    # Part A-2: Core Work (3문항)
    {"id": "A7", "part": "A-2", "section": "Core Work", "type": "pattern",
     "text": "본업 산출물 생산", "sub": "코드/기획서/시안/보고서/논문", "color": "#4fc3f7"},
    {"id": "A8", "part": "A-2", "section": "Core Work", "type": "pattern",
     "text": "본업 품질 검증·리뷰", "sub": "코드리뷰/정합성체크/UI검증/결과검증", "color": "#4fc3f7"},
    {"id": "A9", "part": "A-2", "section": "Core Work", "type": "pattern",
     "text": "우선순위·의사결정", "sub": "백로그순위/로드맵/방향성 판단", "color": "#4fc3f7"},
    # Part B: AI 활용 행동 (8문항)
    {"id": "B1", "part": "B", "section": "CE 행동", "type": "likert", "color": "#ffd54f",
     "text": "업무에 필요한 정보를 AI로 수집·정리한다"},
    {"id": "B2", "part": "B", "section": "CE 행동", "type": "likert", "color": "#ffd54f",
     "text": "AI를 활용해 여러 출처의 정보를 하나의 맥락으로 연결한다"},
    {"id": "B3", "part": "B", "section": "CE 행동", "type": "likert", "color": "#ffd54f",
     "text": "AI가 정리한 맥락 정보를 팀원에게 공유하여 의사결정에 활용한다"},
    {"id": "B4", "part": "B", "section": "CE 행동", "type": "likert", "color": "#ffd54f",
     "text": "AI에게 더 나은 결과를 얻기 위해 프롬프트·맥락을 의도적으로 설계한다"},
    {"id": "B5", "part": "B", "section": "CW 행동", "type": "likert", "color": "#4fc3f7",
     "text": "AI가 만든 결과물을 수정 없이 그대로 사용한 적이 있다"},
    {"id": "B6", "part": "B", "section": "CW 행동", "type": "likert", "color": "#4fc3f7",
     "text": "AI 결과물이 틀렸을 때 직접 발견해서 고친 경험이 있다"},
    {"id": "B7", "part": "B", "section": "CW 행동", "type": "likert", "color": "#4fc3f7",
     "text": "AI에게 같은 작업을 여러 번 다시 시켜보며 최적 결과를 찾는다"},
    {"id": "B8", "part": "B", "section": "CW 행동", "type": "likert", "color": "#4fc3f7",
     "text": "AI 없이는 처리하기 어려웠을 본업 작업을 AI 덕분에 수행한다"},
    # Part C: 자율성 (12문항)
    {"id": "C1", "part": "C", "section": "의사결정 자율성", "type": "likert", "color": "#00D4FF",
     "text": "나는 업무 관련 결정을 스스로 내릴 수 있다"},
    {"id": "C2", "part": "C", "section": "의사결정 자율성", "type": "likert", "color": "#00D4FF",
     "text": "목표 달성 방법을 자율적으로 판단한다"},
    {"id": "C3", "part": "C", "section": "의사결정 자율성", "type": "likert", "color": "#00D4FF",
     "text": "관리자 승인 없이 일상 업무를 결정한다"},
    {"id": "C4", "part": "C", "section": "업무방식 자율성", "type": "likert", "color": "#00E676",
     "text": "업무 수행 방식을 내가 선택한다"},
    {"id": "C5", "part": "C", "section": "업무방식 자율성", "type": "likert", "color": "#00E676",
     "text": "사용할 도구/절차를 스스로 정한다"},
    {"id": "C6", "part": "C", "section": "업무방식 자율성", "type": "likert", "color": "#00E676",
     "text": "기존 절차를 개선하거나 변경할 자유가 있다"},
    {"id": "C7", "part": "C", "section": "일정 자율성", "type": "likert", "color": "#00E676",
     "text": "업무 순서를 스스로 정한다"},
    {"id": "C8", "part": "C", "section": "일정 자율성", "type": "likert", "color": "#00E676",
     "text": "시간 배분을 자유롭게 조절한다"},
    {"id": "C9", "part": "C", "section": "일정 자율성", "type": "likert", "color": "#00E676",
     "text": "업무 일정을 주도적으로 계획한다"},
    {"id": "C10", "part": "C", "section": "AI 기여 자율성", "type": "likert", "color": "#ab47bc",
     "text": "AI 도입 이후, 이전보다 더 많은 결정을 스스로 내리게 되었다"},
    {"id": "C11", "part": "C", "section": "AI 기여 자율성", "type": "likert", "color": "#ab47bc",
     "text": "AI가 제공한 정보 덕분에 상급자에게 확인받지 않아도 되는 일이 늘었다"},
    {"id": "C12", "part": "C", "section": "AI 기여 자율성", "type": "likert", "color": "#ab47bc",
     "text": "AI가 없었다면 지금처럼 자율적으로 일하기 어려웠을 것이다"},
    # Part D: 정보 투명성 + AI 인식 (10문항)
    {"id": "D1", "part": "D", "section": "정보 투명성", "type": "likert", "color": "#66bb6a",
     "text": "업무에 필요한 맥락 정보(배경·목적·근거)를 나는 충분히 얻을 수 있다"},
    {"id": "D2", "part": "D", "section": "정보 투명성", "type": "likert", "color": "#66bb6a",
     "text": "이전에는 접근하기 어려웠던 정보에 지금은 접근할 수 있다"},
    {"id": "D3", "part": "D", "section": "정보 투명성", "type": "likert", "color": "#66bb6a",
     "text": "AI가 정리한 정보를 보고 스스로 판단을 내린 경험이 있다"},
    {"id": "D4", "part": "D", "section": "AI 인식", "type": "likert", "color": "#FFD700",
     "text": "AI 덕분에 혼자서도 판단을 내릴 수 있는 일이 늘었다"},
    {"id": "D5", "part": "D", "section": "AI 인식", "type": "likert", "color": "#FFD700",
     "text": "AI가 추천하거나 정리한 것의 이유를 납득할 수 있다"},
    {"id": "D6", "part": "D", "section": "감시 체감", "type": "likert", "color": "#ef5350",
     "text": "AI가 업무를 추적하면서 내 일이 더 들여다보여지는 느낌이 든다"},
    {"id": "D7", "part": "D", "section": "감시 체감", "type": "likert", "color": "#ef5350",
     "text": "AI가 수집한 데이터가 성과 평가에 활용될 수 있다는 생각이 든다"},
    {"id": "D8", "part": "D", "section": "감시 체감", "type": "likert", "color": "#ef5350",
     "text": "AI 도구 사용 기록이 남는 것에 대해 신경 쓰인다"},
    {"id": "D9", "part": "D", "section": "위임 전환", "type": "likert", "color": "#78909c",
     "text": "AI에게 맡겨도 될 일인데 내가 직접 하게 되는 일이 있다"},
    {"id": "D10", "part": "D", "section": "위임 전환", "type": "likert", "color": "#78909c",
     "text": "AI에게 맡기면서 내가 직접 하는 일이 줄었다"},
    # Part E: 주관식 (3문항)
    {"id": "E1", "part": "E", "section": "주관식", "type": "text", "color": "#78909c",
     "text": "최근 1개월 이내에 AI 때문에 업무 방식이 달라진 구체적 경험이 있다면 적어주세요."},
    {"id": "E2", "part": "E", "section": "주관식", "type": "text", "color": "#78909c",
     "text": "AI 도입 전과 비교해서 리더(관리자)의 역할에서 가장 크게 변한 점은?"},
    {"id": "E3", "part": "E", "section": "주관식", "type": "text", "color": "#78909c",
     "text": "AI가 정보를 더 잘 정리해줌으로써 스스로 판단할 수 있게 된 사례, 또는 자율성이 줄어든 사례가 있다면 적어주세요."},
]

PARTS = [
    {"id": "A-1", "name": "Context Engineering", "desc": "AI로 맥락을 구성하는 활동", "color": "#ffd54f"},
    {"id": "A-2", "name": "Core Work", "desc": "AI로 본업을 수행하는 활동", "color": "#4fc3f7"},
    {"id": "B", "name": "AI 활용 행동", "desc": "AI를 어떻게 쓰는가", "color": "#90a4ae"},
    {"id": "C", "name": "자율성", "desc": "기준선 + AI 기여", "color": "#00D4FF"},
    {"id": "D", "name": "투명성 + AI 인식", "desc": "정보 접근 + 감시 체감", "color": "#66bb6a"},
    {"id": "E", "name": "주관식", "desc": "에피소드와 사례", "color": "#78909c"},
]


# ── 결과 산출 ──
def safe_mean(values):
    nums = [v for v in values if v is not None]
    return round(sum(nums) / len(nums), 2) if nums else None


def calculate_results(form_data: dict) -> dict:
    # Parse pattern answers (A1-A9)
    a_scores = {}
    agencies = []
    for i in range(1, 10):
        key = f"A{i}"
        val = form_data.get(key, "").strip()
        if val in ("na", ""):
            a_scores[key] = None
        elif val.isdigit():
            a_scores[key] = int(val)
            agency = form_data.get(f"{key}_agency", "")
            if agency:
                agencies.append(agency)
        else:
            a_scores[key] = None

    # CE Pattern (A1-A6)
    ce_vals = [a_scores[f"A{i}"] for i in range(1, 7)]
    ce_avg = safe_mean(ce_vals)
    ce_level = pattern_level(ce_avg) if ce_avg is not None else None

    # CW Pattern (A7-A9)
    cw_vals = [a_scores[f"A{i}"] for i in range(7, 10)]
    cw_avg = safe_mean(cw_vals)
    cw_level = pattern_level(cw_avg) if cw_avg is not None else None

    # Overall Pattern
    all_vals = [v for v in a_scores.values() if v is not None]
    overall_avg = safe_mean(all_vals)
    overall_level = pattern_level(overall_avg) if overall_avg is not None else None

    # Agency Direction
    a_count = sum(1 for a in agencies if a == "a")
    total_agency = len(agencies)
    bu_pct = round(a_count / total_agency * 100) if total_agency > 0 else 0
    if bu_pct >= 70:
        agency_type = "자발 주도형"
    elif bu_pct >= 40:
        agency_type = "혼합형"
    else:
        agency_type = "시스템 주도형"

    # Likert scores
    def likert(key):
        v = form_data.get(key, "")
        return int(v) if v.isdigit() else None

    # Part B
    ce_behavior = safe_mean([likert(f"B{i}") for i in range(1, 5)])
    b5, b6, b7, b8 = likert("B5"), likert("B6"), likert("B7"), likert("B8")

    # Part C
    decision = safe_mean([likert(f"C{i}") for i in range(1, 4)])
    method = safe_mean([likert(f"C{i}") for i in range(4, 7)])
    schedule = safe_mean([likert(f"C{i}") for i in range(7, 10)])
    baseline = safe_mean([likert(f"C{i}") for i in range(1, 10)])
    ai_contrib = safe_mean([likert(f"C{i}") for i in range(10, 13)])

    # Part D
    transparency = safe_mean([likert(f"D{i}") for i in range(1, 4)])
    d4, d5 = likert("D4"), likert("D5")
    surveillance = safe_mean([likert(f"D{i}") for i in range(6, 9)])
    d6, d7, d8 = likert("D6"), likert("D7"), likert("D8")
    d9, d10 = likert("D9"), likert("D10")

    return {
        "a_scores": a_scores,
        "ce": {"avg": ce_avg, "level": ce_level, "name": PATTERN_NAMES.get(ce_level, "N/A")},
        "cw": {"avg": cw_avg, "level": cw_level, "name": PATTERN_NAMES.get(cw_level, "N/A")},
        "overall": {"avg": overall_avg, "level": overall_level, "name": PATTERN_NAMES.get(overall_level, "N/A")},
        "agency": {"type": agency_type, "bottom_up_pct": bu_pct, "top_down_pct": 100 - bu_pct},
        "behavior": {"ce": ce_behavior, "delegation": b5, "validation": b6, "optimization": b7, "expansion": b8},
        "autonomy": {"decision": decision, "method": method, "schedule": schedule, "baseline": baseline, "ai_contrib": ai_contrib},
        "transparency": transparency,
        "surveillance": {"overall": surveillance, "visibility": d6, "eval_concern": d7, "restraint": d8},
        "ai_awareness": {"autonomy_felt": d4, "ai_understanding": d5},
        "delegation": {"hurdle": d9, "effect": d10},
        "open_ended": {
            "E1": form_data.get("E1", ""),
            "E2": form_data.get("E2", ""),
            "E3": form_data.get("E3", ""),
        },
    }


# ── Routes ──
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if DEV_MODE and not user:
        user = {"name": "Dev User", "email": "dev@test.com", "nickname": "테스터"}
        request.session["user"] = user
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/login")
async def login(request: Request):
    if DEV_MODE:
        request.session["user"] = {"name": "Dev User", "email": "dev@test.com", "nickname": "테스터"}
        return RedirectResponse(url="/")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BASE_URL}/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(url="/")
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{BASE_URL}/callback", "grant_type": "authorization_code",
        })
        token_data = token_resp.json()
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data.get('access_token', '')}"},
        )
        userinfo = userinfo_resp.json()
    name = userinfo.get("name", "")
    request.session["user"] = {
        "name": name, "email": userinfo.get("email", ""),
        "nickname": MEMBER_MAP.get(name, name),
    }
    return RedirectResponse(url="/")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


@app.get("/survey", response_class=HTMLResponse)
async def survey(request: Request):
    user = request.session.get("user")
    if not user and not DEV_MODE:
        return RedirectResponse(url="/")
    if DEV_MODE and not user:
        user = {"name": "Dev User", "email": "dev@test.com", "nickname": "테스터"}
        request.session["user"] = user
    return templates.TemplateResponse("survey.html", {
        "request": request,
        "user": user,
        "questions": QUESTIONS,
        "parts": PARTS,
        "pattern_options": PATTERN_OPTIONS,
        "agency_member": AGENCY_MEMBER,
        "agency_leader": AGENCY_LEADER,
    })


@app.post("/submit")
async def submit(request: Request):
    user = request.session.get("user")
    if not user and not DEV_MODE:
        return RedirectResponse(url="/")
    if DEV_MODE and not user:
        user = {"name": "Dev User", "email": "dev@test.com", "nickname": "테스터"}

    form = await request.form()
    form_data = dict(form)
    results = calculate_results(form_data)
    results["nickname"] = user.get("nickname", "")
    results["role"] = form_data.get("role", "구성원")
    results["job"] = form_data.get("job", "")
    results["org_size"] = form_data.get("org_size", "")
    results["ai_duration"] = form_data.get("ai_duration", "")
    results["raw"] = form_data
    results["surveyed_at"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    request.session["results"] = results
    return RedirectResponse(url="/result", status_code=303)


@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    user = request.session.get("user")
    results = request.session.get("results")
    if not results:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("result.html", {
        "request": request, "user": user, "r": results,
        "now": results.get("surveyed_at", ""),
        "questions": QUESTIONS, "parts": PARTS,
        "pattern_options": PATTERN_OPTIONS,
    })


@app.get("/guide", response_class=HTMLResponse)
async def guide(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("guide.html", {"request": request, "user": user})


@app.get("/docs/coverage-map", response_class=HTMLResponse)
async def coverage_map(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse("coverage.html", {"request": request, "user": user})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
