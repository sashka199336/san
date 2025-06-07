import pytest
from san import (
    parse_csv, PayoutReport, AvgHourlyRateByDepartmentReport, CountByDepartmentReport,
    TopPayoutReport, TopRateReport, TotalPayoutByDepartmentReport
)

SAMPLE_CSV = """id,email,name,department,hours_worked,hourly_rate
1,alice@example.com,Alice Johnson,Marketing,160,50
2,bob@example.com,Bob Smith,Design,150,40
3,carol@example.com,Carol Williams,Design,170,60
"""

SAMPLE_CSV_RATE = """id,name,department,hours_worked,rate
1,Alice,Dev,100,50
2,Bob,Dev,90,75
"""

def get_rows(csv_text):
    from io import StringIO
    return parse_csv(StringIO(csv_text))

def test_parse_csv_basic():
    rows = get_rows(SAMPLE_CSV)
    assert len(rows) == 3
    assert rows[0]['name'] == "Alice Johnson"

def test_payout_report():
    rows = get_rows(SAMPLE_CSV)
    report = PayoutReport()
    result = report.generate(rows)
    assert "payouts" in result
    assert abs(result['payouts'][0]['payout'] - 8000.0) < 0.01

def test_payout_report_with_rate_column():
    rows = get_rows(SAMPLE_CSV_RATE)
    report = PayoutReport()
    result = report.generate(rows)
    assert "payouts" in result
    assert len(result['payouts']) == 2

def test_avg_hourly_rate_by_department_report():
    rows = get_rows(SAMPLE_CSV)
    report = AvgHourlyRateByDepartmentReport()
    res = report.generate(rows)
    assert "average_hourly_rate_by_department" in res
    deps = res["average_hourly_rate_by_department"]
    assert any(d["department"] == "Design" for d in deps)

def test_count_by_department_report():
    rows = get_rows(SAMPLE_CSV)
    report = CountByDepartmentReport()
    res = report.generate(rows)
    assert "count_by_department" in res
    assert res["count_by_department"]["Design"] == 2

def test_top_payout_report():
    rows = get_rows(SAMPLE_CSV)
    report = TopPayoutReport()
    res = report.generate(rows)
    assert res['top_payout']["name"] == "Carol Williams"

def test_top_rate_report():
    rows = get_rows(SAMPLE_CSV)
    report = TopRateReport()
    res = report.generate(rows)
    assert res['top_rate']["rate"] == 60.0

def test_total_payout_by_department_report():
    rows = get_rows(SAMPLE_CSV)
    report = TotalPayoutByDepartmentReport()
    res = report.generate(rows)
    assert "total_payout_by_department" in res
    assert "Design" in res["total_payout_by_department"]

# Проверка пустых данных и плохих значений
def test_empty_data():
    rows = get_rows("")
    assert rows == []
    for report_cls in [PayoutReport, AvgHourlyRateByDepartmentReport, CountByDepartmentReport,
                       TopPayoutReport, TopRateReport, TotalPayoutByDepartmentReport]:
        assert isinstance(report_cls().generate(rows), dict)

def test_bad_hour_values():
    from io import StringIO
    csv_data = """id,name,department,hours_worked,rate
1,Olga,TestDept,not_a_number,99
"""
    rows = parse_csv(StringIO(csv_data))
    # Убеждаемся, что метод не рушится на плохих числах
    for report_cls in [PayoutReport, TopPayoutReport, TotalPayoutByDepartmentReport]:
        assert isinstance(report_cls().generate(rows), dict)

def test_different_salary_column():
    from io import StringIO
    csv_data = """id,name,department,hours_worked,salary
1,Max,Account,10,1000
"""
    rows = parse_csv(StringIO(csv_data))
    report = PayoutReport()
    result = report.generate(rows)
    assert "payouts" in result
    assert abs(result['payouts'][0]['payout'] - 10000.0) < 0.01