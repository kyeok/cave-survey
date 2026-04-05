"""API 엔드포인트 테스트"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DEV_MODE"] = "true"

import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── 페이지 접근 ──

@pytest.mark.anyio
async def test_home_page(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "CAVE" in r.text


@pytest.mark.anyio
async def test_survey_page(client):
    r = await client.get("/survey")
    assert r.status_code == 200
    assert "Part A" in r.text or "Context Engineering" in r.text


@pytest.mark.anyio
async def test_guide_page(client):
    r = await client.get("/guide")
    assert r.status_code == 200
    assert "AI Ops Pattern" in r.text


@pytest.mark.anyio
async def test_coverage_page(client):
    r = await client.get("/docs/coverage-map")
    assert r.status_code == 200
    assert "커버리지" in r.text


# ── 게스트 ──

@pytest.mark.anyio
async def test_guest_redirect(client):
    r = await client.get("/guest", follow_redirects=False)
    assert r.status_code == 307
    assert "/survey" in r.headers.get("location", "")


# ── 설문 제출 ──

def _full_form_data():
    data = {"role": "구성원", "org_size": "11~30명", "ai_duration": "1년+", "nickname": "테스터"}
    for i in range(1, 10):
        data[f"A{i}"] = "2"
        data[f"A{i}_agency"] = "a"
    for i in range(1, 9):
        data[f"B{i}"] = "3"
    for i in range(1, 13):
        data[f"C{i}"] = "4"
    for i in range(1, 13):
        data[f"D{i}"] = "3"
    data["E1"] = "테스트"
    data["E2"] = "테스트"
    data["E3"] = "테스트"
    return data


@pytest.mark.anyio
async def test_submit_valid(client):
    r = await client.post("/submit", data=_full_form_data(), follow_redirects=False)
    assert r.status_code == 303
    assert "/result" in r.headers.get("location", "")


@pytest.mark.anyio
async def test_submit_partial(client):
    """일부 빈 값이어도 에러 없이 처리"""
    data = _full_form_data()
    data["A1"] = ""
    data["B1"] = ""
    data["C1"] = ""
    r = await client.post("/submit", data=data, follow_redirects=False)
    assert r.status_code == 303


@pytest.mark.anyio
async def test_submit_all_na(client):
    """A1~A9 전부 N/A"""
    data = _full_form_data()
    for i in range(1, 10):
        data[f"A{i}"] = "na"
        data.pop(f"A{i}_agency", None)
    r = await client.post("/submit", data=data, follow_redirects=False)
    assert r.status_code == 303


@pytest.mark.anyio
async def test_result_page(client):
    """제출 후 결과 페이지 접근"""
    # 먼저 제출
    await client.post("/submit", data=_full_form_data())
    # 결과 페이지
    r = await client.get("/result")
    assert r.status_code == 200
    assert "AI Ops Pattern" in r.text or "radarPattern" in r.text
