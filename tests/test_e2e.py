"""FE End-to-End 테스트 (Playwright)"""
import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DEV_MODE"] = "true"

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

PORT = 18765
BASE = f"http://localhost:{PORT}"


@pytest.fixture(scope="module", autouse=True)
def server():
    from main import app
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    time.sleep(1)
    yield
    srv.should_exit = True


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    p = browser.new_page()
    yield p
    p.close()


def active_slide(page):
    """현재 활성 슬라이드 locator"""
    return page.locator(".slide.active")


def go_to_survey(page):
    """설문 진입 + 응답자 정보 입력 + 다음"""
    page.goto(f"{BASE}/survey")
    page.locator(".seg-btn", has_text="구성원").click()
    page.locator(".seg-btn", has_text="11~30명").click()
    page.locator(".seg-btn", has_text="1년+").click()
    active_slide(page).locator("button", has_text="다음").click()
    page.wait_for_timeout(500)


def click_pattern_p0(page, count=1):
    """현재 보이는 Pattern 문항에서 P0 선택 (count번 반복)"""
    for _ in range(count):
        active_slide(page).locator(".choice", has_text="AI 미사용").click()
        page.wait_for_timeout(450)


def click_likert(page, val="3", count=1):
    """현재 보이는 Likert에서 val 선택 (count번 반복)"""
    for _ in range(count):
        active_slide(page).locator(f".likert-btn .l-num", has_text=val).click()
        page.wait_for_timeout(400)


def skip_text(page, count=1):
    """주관식 건너뛰기 (count번 반복)"""
    for _ in range(count):
        active_slide(page).locator("button", has_text="건너뛰기").click()
        page.wait_for_timeout(350)


# ── 페이지 접근 ──

def test_home_loads(page):
    page.goto(BASE)
    assert page.title() == "CAVE Survey — AI Ops Pattern 진단"


def test_guide_loads(page):
    page.goto(f"{BASE}/guide")
    assert page.locator("text=AI Ops Pattern이란?").first.is_visible()


def test_coverage_loads(page):
    page.goto(f"{BASE}/docs/coverage-map")
    assert page.locator("text=커버리지").first.is_visible()


# ── 설문 진입 ──

def test_survey_starts_at_info(page):
    page.goto(f"{BASE}/survey")
    assert page.locator("text=기본 정보를 알려주세요").is_visible()


def test_guest_to_survey(page):
    page.goto(f"{BASE}/guest")
    page.wait_for_url(f"**/survey")
    assert page.locator("text=기본 정보를 알려주세요").is_visible()


# ── 응답자 정보 ──

def test_role_badge(page):
    page.goto(f"{BASE}/survey")
    page.locator(".seg-btn", has_text="리더").click()
    badge = page.locator("#roleBadge")
    assert badge.is_visible()
    assert badge.text_content() == "리더"


def test_segmented_buttons(page):
    page.goto(f"{BASE}/survey")
    btn = page.locator(".seg-btn", has_text="11~30명")
    btn.click()
    assert "selected" in btn.get_attribute("class")


# ── Pattern + Agency ──

def test_pattern_p0_auto_advance(page):
    """P0 선택 → Agency 없이 자동 전환"""
    go_to_survey(page)
    # A1에 있는지 확인
    assert active_slide(page).locator("[data-qid='A1']").or_(active_slide(page).locator("text=일정 관리")).first.is_visible()
    # P0 선택
    active_slide(page).locator(".choice", has_text="AI 미사용").click()
    page.wait_for_timeout(500)
    # A2로 이동
    assert active_slide(page).locator("text=업무 추적").is_visible()


def test_pattern_shows_agency(page):
    """P2 선택 → Agency concept map 표시"""
    go_to_survey(page)
    active_slide(page).locator(".choice", has_text="AI 협업").click()
    page.wait_for_timeout(400)
    assert active_slide(page).locator(".cmap-node").first.is_visible()


def test_agency_click_advances(page):
    """Agency 노드 클릭 → 다음 문항으로 전환"""
    go_to_survey(page)
    active_slide(page).locator(".choice", has_text="AI 협업").click()
    page.wait_for_timeout(400)
    active_slide(page).locator(".cmap-node", has_text="개인 활용").click()
    page.wait_for_timeout(500)
    assert active_slide(page).locator("text=업무 추적").is_visible()


# ── Likert ──

def test_likert_auto_advance(page):
    """Likert 선택 → 자동 전환"""
    go_to_survey(page)
    click_pattern_p0(page, 9)  # A1~A9 전부 P0
    # B1 Likert
    active_slide(page).locator(".likert-btn .l-num", has_text="4").click()
    page.wait_for_timeout(400)
    # B2로 이동
    assert active_slide(page).locator("text=여러 출처의 정보").is_visible()


# ── 전체 흐름 ──

def test_full_survey_to_result(page):
    """44문항 전체 → 결과 페이지 도달"""
    go_to_survey(page)
    click_pattern_p0(page, 9)    # A1~A9
    click_likert(page, "3", 8)   # B1~B8
    click_likert(page, "4", 12)  # C1~C12
    click_likert(page, "3", 12)  # D1~D12
    skip_text(page, 3)           # E1~E3 → 자동 제출
    page.wait_for_url("**/result", timeout=5000)
    assert page.locator("text=AI Ops Pattern").first.is_visible()


def test_result_has_radar_chart(page):
    """결과 페이지에 레이더 차트 존재"""
    go_to_survey(page)
    click_pattern_p0(page, 9)
    click_likert(page, "3", 32)
    skip_text(page, 3)
    page.wait_for_url("**/result", timeout=5000)
    assert page.locator("#radarPattern").is_visible()
    assert page.locator("#radarProfile").is_visible()


def test_pdf_button_exists(page):
    """결과 페이지에 PDF 다운로드 버튼 존재"""
    go_to_survey(page)
    click_pattern_p0(page, 9)
    click_likert(page, "3", 32)
    skip_text(page, 3)
    page.wait_for_url("**/result", timeout=5000)
    assert page.locator("text=PDF 다운로드").is_visible()
