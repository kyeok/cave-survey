"""산출 로직 단위 테스트"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import pattern_level, safe_mean, calculate_results


# ── pattern_level 경계값 ──

def test_pattern_level_p0():
    assert pattern_level(0.0) == 0
    assert pattern_level(0.4) == 0

def test_pattern_level_p1():
    assert pattern_level(0.5) == 1
    assert pattern_level(1.0) == 1
    assert pattern_level(1.4) == 1

def test_pattern_level_p2():
    assert pattern_level(1.5) == 2
    assert pattern_level(2.0) == 2
    assert pattern_level(2.4) == 2

def test_pattern_level_p3():
    assert pattern_level(2.5) == 3
    assert pattern_level(3.0) == 3
    assert pattern_level(3.4) == 3

def test_pattern_level_p4():
    assert pattern_level(3.5) == 4
    assert pattern_level(4.0) == 4


# ── safe_mean ──

def test_safe_mean_normal():
    assert safe_mean([1, 2, 3]) == 2.0

def test_safe_mean_with_none():
    assert safe_mean([1, None, 3]) == 2.0

def test_safe_mean_all_none():
    assert safe_mean([None, None]) is None

def test_safe_mean_empty():
    assert safe_mean([]) is None


# ── calculate_results 전체 흐름 ──

def _make_form_data(**overrides):
    """기본 전체 응답 데이터 생성"""
    data = {}
    # Part A: Pattern + Agency
    for i in range(1, 10):
        data[f"A{i}"] = "2"
        data[f"A{i}_agency"] = "a"
    # Part B: Likert
    for i in range(1, 9):
        data[f"B{i}"] = "3"
    # Part C: Likert
    for i in range(1, 13):
        data[f"C{i}"] = "4"
    # Part D: Likert
    for i in range(1, 13):
        data[f"D{i}"] = "3"
    # Part E: Text
    data["E1"] = "테스트"
    data["E2"] = "테스트"
    data["E3"] = "테스트"
    data.update(overrides)
    return data


def test_calculate_ce_pattern():
    r = calculate_results(_make_form_data())
    assert r["ce"]["level"] == 2
    assert r["ce"]["name"] == "AI 협업"
    assert r["ce"]["avg"] == 2.0


def test_calculate_cw_pattern():
    r = calculate_results(_make_form_data())
    assert r["cw"]["level"] == 2
    assert r["cw"]["avg"] == 2.0


def test_calculate_overall_pattern():
    r = calculate_results(_make_form_data())
    assert r["overall"]["level"] == 2
    assert r["overall"]["avg"] == 2.0


def test_calculate_na_excluded():
    """N/A 응답은 평균 계산에서 제외"""
    data = _make_form_data(A1="na", A2="na", A3="na", A4="na", A5="na", A6="na")
    r = calculate_results(data)
    # CE는 전부 N/A → None
    assert r["ce"]["avg"] is None
    assert r["ce"]["level"] is None
    # CW는 여전히 2
    assert r["cw"]["level"] == 2


def test_calculate_empty_values():
    """빈 값도 에러 없이 처리"""
    data = _make_form_data(A1="", A2="", B1="", C1="")
    r = calculate_results(data)
    assert r["overall"]["avg"] is not None or r["overall"]["avg"] is None  # 에러만 안 나면 OK


def test_agency_bottom_up():
    """전부 a → 자발 주도형"""
    r = calculate_results(_make_form_data())
    assert r["agency"]["type"] == "자발 주도형"
    assert r["agency"]["bottom_up_pct"] == 100


def test_agency_top_down():
    """전부 c → 시스템 주도형"""
    data = _make_form_data()
    for i in range(1, 10):
        data[f"A{i}_agency"] = "c"
    r = calculate_results(data)
    assert r["agency"]["type"] == "시스템 주도형"
    assert r["agency"]["bottom_up_pct"] == 0


def test_agency_mixed():
    """a 5개 + c 4개 → 혼합형 (55%)"""
    data = _make_form_data()
    for i in range(1, 6):
        data[f"A{i}_agency"] = "a"
    for i in range(6, 10):
        data[f"A{i}_agency"] = "c"
    r = calculate_results(data)
    assert r["agency"]["type"] == "혼합형"


def test_autonomy_scores():
    """자율성 기준선 + AI 기여"""
    r = calculate_results(_make_form_data())
    assert r["autonomy"]["decision"] == 4.0
    assert r["autonomy"]["method"] == 4.0
    assert r["autonomy"]["schedule"] == 4.0
    assert r["autonomy"]["baseline"] == 4.0
    assert r["autonomy"]["ai_contrib"] == 4.0


def test_transparency_surveillance():
    """투명성 + 감시 체감"""
    r = calculate_results(_make_form_data())
    assert r["transparency"] == 3.0
    assert r["surveillance"]["overall"] == 3.0


def test_psych_safety():
    """심리적 안전감"""
    data = _make_form_data(D11="5", D12="4")
    r = calculate_results(data)
    assert r["psych_safety"]["overall"] == 4.5
    assert r["psych_safety"]["openness"] == 5
    assert r["psych_safety"]["no_blame"] == 4


def test_open_ended():
    """주관식 응답 보존"""
    r = calculate_results(_make_form_data(E1="에피소드", E2="리더변화", E3="사례"))
    assert r["open_ended"]["E1"] == "에피소드"
    assert r["open_ended"]["E2"] == "리더변화"
    assert r["open_ended"]["E3"] == "사례"
