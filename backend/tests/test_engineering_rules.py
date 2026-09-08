from app.db.models import ParameterValue
from app.services.engineering_rules import check_breaker_sizing, check_current_consistency, run_calc_checks


def _pv(name, value, unit=None):
    return ParameterValue(equipment_id=1, document_id=1, name=name, value=str(value), numeric_value=value, unit=unit)


def test_current_consistency_flags_mismatch():
    # 15kW / 380V 3-phase @ pf 0.85, eff 0.9 -> ~26.7A expected, but document says 60A
    params = [_pv("Power", 15, "kW"), _pv("Voltage", 380, "V"), _pv("Current", 60, "A")]
    finding = check_current_consistency(params)
    assert finding is not None
    assert finding.check == "current_vs_power"
    assert finding.severity == "MEDIUM"
    assert 20 < finding.calculated_value < 35


def test_current_consistency_accepts_matching_value():
    # ~26.7A expected — report a value within tolerance
    params = [_pv("Power", 15, "kW"), _pv("Voltage", 380, "V"), _pv("Current", 27, "A")]
    finding = check_current_consistency(params)
    assert finding is None


def test_current_consistency_skips_when_inputs_missing():
    assert check_current_consistency([_pv("Power", 15, "kW")]) is None


def test_breaker_undersized():
    params = [_pv("Current", 30, "A"), _pv("Breaker Size", 30, "A")]
    finding = check_breaker_sizing(params)
    assert finding is not None
    assert finding.check == "breaker_undersized"
    assert finding.severity == "HIGH"


def test_breaker_oversized():
    params = [_pv("Current", 10, "A"), _pv("Breaker Size", 100, "A")]
    finding = check_breaker_sizing(params)
    assert finding is not None
    assert finding.check == "breaker_oversized"
    assert finding.severity == "LOW"


def test_breaker_within_normal_range():
    params = [_pv("Current", 30, "A"), _pv("Breaker Size", 40, "A")]
    assert check_breaker_sizing(params) is None


def test_run_calc_checks_combines_both():
    params = [
        _pv("Power", 15, "kW"), _pv("Voltage", 380, "V"), _pv("Current", 60, "A"),
        _pv("Breaker Size", 32, "A"),
    ]
    findings = run_calc_checks(params)
    checks = {f.check for f in findings}
    assert "current_vs_power" in checks
    # breaker (32A) vs reported current (60A) is undersized too
    assert "breaker_undersized" in checks
