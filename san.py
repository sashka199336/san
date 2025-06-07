import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, TextIO

# Парсер
def parse_csv(file: TextIO) -> List[Dict[str, str]]:

    lines = file.read().splitlines()
    if not lines:
        return []
    headers = [header.strip() for header in lines[0].split(",")]
    data = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = [value.strip() for value in line.split(",")]
        if len(values) != len(headers):
            continue  # пропускаем битые строки
        data.append(dict(zip(headers, values)))
    return data

# Загрузка сотрудников из файлов
def load_employees(filepaths: List[str]) -> List[Dict[str, str]]:
    """
    Объедениение сотрудников в 1 список.
    """
    employees = []
    for filepath in filepaths:
        with open(filepath, encoding="utf-8") as f:
            employees.extend(parse_csv(f))
    return employees

# --------- Базовый класс-отчёт ---------
class Report:

    def generate(self, data: List[Dict[str, str]]) -> dict:
        raise NotImplementedError("Report must implement .generate()")

# Отчёт по выплатам
class PayoutReport(Report):
    """
    формирует от чёт по влатам на каждого сотрудника.
    """
    PAY_RATE_KEYS = {"hourly_rate", "rate", "salary"}

    def get_pay_rate(self, row: Dict[str, str]) -> Optional[float]:
        """
        Определяет ставку для сотрудника из возможных вариантов названия колонки.
        """
        for key in self.PAY_RATE_KEYS:
            if key in row:
                try:
                    return float(row[key])
                except ValueError:
                    return None
        return None

    def generate(self, data: List[Dict[str, str]]) -> dict:
        """
        счет выплат
        """
        results = []
        for row in data:
            try:
                hours = float(row.get("hours_worked", "0"))
            except ValueError:
                continue
            rate = self.get_pay_rate(row)
            if rate is None:
                continue
            payout = hours * rate
            results.append({
                "id": row.get("id"),
                "name": row.get("name"),
                "department": row.get("department"),
                "hours_worked": hours,
                "rate": rate,
                "payout": payout
            })
        return {"payouts": results}

# Отчёт по среднему rate по отделам
class AvgHourlyRateByDepartmentReport(Report):
    """
     тчёт, средний rate по каждому департаменту.
    """
    PAY_RATE_KEYS = {"hourly_rate", "rate", "salary"}

    def get_pay_rate(self, row: Dict[str, str]) -> Optional[float]:
        """
        Определяет ставку для сотрудника (ищет по всем допустимым ключам).
        """
        for key in self.PAY_RATE_KEYS:
            if key in row:
                try:
                    return float(row[key])
                except ValueError:
                    return None
        return None

    def generate(self, data: List[Dict[str, str]]) -> dict:
        dep_rates: Dict[str, float] = {}
        dep_counts: Dict[str, int] = {}
        for row in data:
            department = row.get("department", "unknown")
            rate = self.get_pay_rate(row)
            if rate is None:
                continue
            dep_rates.setdefault(department, 0.0)
            dep_counts.setdefault(department, 0)
            dep_rates[department] += rate
            dep_counts[department] += 1

        result = []
        for department in dep_rates:
            avg_rate = dep_rates[department] / dep_counts[department]
            result.append({
                "department": department,
                "average_rate": avg_rate,
                "employees": dep_counts[department]
            })
        return {"average_hourly_rate_by_department": result}

#  Количество сотрудников по каждому отделу
class CountByDepartmentReport(Report):
    """
    Количество сотрудников в каждом отделе.
    """
    def generate(self, data: List[Dict[str, str]]) -> dict:
        counts = {}
        for row in data:
            department = row.get("department", "unknown")
            counts[department] = counts.get(department, 0) + 1
        return {"count_by_department": counts}

# Сотрудник с самой большой суммой выплаты
class TopPayoutReport(Report):
    """
    Сотрудник с самой большой суммой выплаты .
    """
    PAY_RATE_KEYS = {"hourly_rate", "rate", "salary"}

    def get_pay_rate(self, row: Dict[str, str]) -> Optional[float]:
        for key in self.PAY_RATE_KEYS:
            if key in row:
                try:
                    return float(row[key])
                except ValueError:
                    continue
        return None

    def generate(self, data: List[Dict[str, str]]) -> dict:
        max_payout = None
        top_row = None
        for row in data:
            try:
                hours = float(row.get("hours_worked", "0"))
            except ValueError:
                continue
            rate = self.get_pay_rate(row)
            if rate is None:
                continue
            payout = hours * rate
            if (max_payout is None) or (payout > max_payout):
                max_payout = payout
                top_row = row
        if top_row:
            return {
                "top_payout": {
                    "name": top_row.get("name"),
                    "department": top_row.get("department"),
                    "payout": max_payout
                }
            }
        else:
            return {"top_payout": None}


class TopRateReport(Report):  # Сотрудник с самой высокой ставкой за чаСЧ

    PAY_RATE_KEYS = {"hourly_rate", "rate", "salary"}

    def get_pay_rate(self, row: Dict[str, str]) -> Optional[float]:
        for key in self.PAY_RATE_KEYS:
            if key in row:
                try:
                    return float(row[key])
                except ValueError:
                    continue
        return None

    def generate(self, data: List[Dict[str, str]]) -> dict:
        max_rate = None
        top_row = None
        for row in data:
            rate = self.get_pay_rate(row)
            if rate is None:
                continue
            if (max_rate is None) or (rate > max_rate):
                max_rate = rate
                top_row = row
        if top_row:
            return {
                "top_rate": {
                    "name": top_row.get("name"),
                    "department": top_row.get("department"),
                    "rate": max_rate
                }
            }
        else:
            return {"top_rate": None}


class TotalPayoutByDepartmentReport(Report):  #  Суммарная выплата по отделам

    PAY_RATE_KEYS = {"hourly_rate", "rate", "salary"}

    def get_pay_rate(self, row: Dict[str, str]) -> Optional[float]:
        for key in self.PAY_RATE_KEYS:
            if key in row:
                try:
                    return float(row[key])
                except ValueError:
                    continue
        return None

    def generate(self, data: List[Dict[str, str]]) -> dict:
        payouts: Dict[str, float] = {}
        for row in data:
            department = row.get("department", "unknown")
            try:
                hours = float(row.get("hours_worked", "0"))
            except ValueError:
                continue
            rate = self.get_pay_rate(row)
            if rate is None:
                continue
            payout = hours * rate
            payouts[department] = payouts.get(department, 0) + payout
        return {"total_payout_by_department": payouts}

#  Виды отчётов
REPORTS: Dict[str, type] = {
    "payout": PayoutReport,  # Детализация выплат по каждому сотруднику
    "avg_hourly_rate_by_department": AvgHourlyRateByDepartmentReport,  # Средняя ставка по отделам
    "count_by_department": CountByDepartmentReport,  # Количество сотрудников по отделам
    "top_payout": TopPayoutReport,  # Сотрудник с самой большой суммой выплаты
    "top_rate": TopRateReport,  # Сотрудник с самой высокой ставкой за час
    "total_payout_by_department": TotalPayoutByDepartmentReport,  # Суммарные выплаты по отделам
}


def print_json(obj, *, pretty: bool = True) -> None:

    print(json.dumps(obj, indent=4 if pretty else None, ensure_ascii=False))


def main(args: Optional[List[str]] = None):

    parser = argparse.ArgumentParser(description="Payroll Report Generator")
    parser.add_argument(
        "files",
        nargs="+",
        help="Input CSV files (data1.csv data2.csv data3.csv)"
    )
    parser.add_argument(
        "--report",
        required=True,
        help=f"Report name. Доступные: {', '.join(REPORTS.keys())}",
        choices=REPORTS.keys()
    )
    parsed = parser.parse_args(args)
    # Проверка наличия файлов
    for path in parsed.files:
        if not Path(path).is_file():
            print(f"Файл не найден: {path}", file=sys.stderr)
            sys.exit(1)
    employees = load_employees(parsed.files)
    report_cls = REPORTS.get(parsed.report)
    if not report_cls:
        print(f"Report '{parsed.report}' не реализован.", file=sys.stderr)
        sys.exit(2)
    report = report_cls()
    result = report.generate(employees)
    print_json(result)

if __name__ == "__main__":
    main()