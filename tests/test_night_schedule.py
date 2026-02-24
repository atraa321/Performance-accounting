from __future__ import annotations

from decimal import Decimal

from openpyxl import Workbook

from app.calc.night_schedule import parse_night_shift_counts


def _build_schedule_file(tmp_path, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "排班表"
    ws.append(["标题"])
    ws.append(["提示"])
    ws.append(["班次说明"])
    ws.append(["部门", "用户ID", "工号", "姓名", "2026/1/1", "2026/1/2", "2026/1/3", "2026/1/4"])
    for row in rows:
        ws.append(row)
    file_path = tmp_path / "schedule.xlsx"
    wb.save(file_path)
    return str(file_path)


def test_parse_doctor_night_shifts(tmp_path):
    file_path = _build_schedule_file(
        tmp_path,
        [
            ["科室", "1", "1", "D1", "夜", "休", "24小时", "主白"],
            ["科室", "2", "2", "D2", "夜班", "主白", "休", "夜"],
            ["科室", "3", "3", "D3", "休", "主白", "休", "主白"],
        ],
    )

    counts = parse_night_shift_counts(file_path, role="doctor")

    assert counts["D1"] == Decimal("2")
    assert counts["D2"] == Decimal("2")
    assert "D3" not in counts


def test_parse_nurse_night_shifts(tmp_path):
    file_path = _build_schedule_file(
        tmp_path,
        [
            ["科室", "1", "1", "N1", "上大", "小", "休", "白班内二科"],
            ["科室", "2", "2", "N2", "通夜", "帮白班", "上休下白", "大"],
            ["科室", "3", "3", "N3", "白班内二科", "帮白班", "休", "休"],
        ],
    )

    counts = parse_night_shift_counts(file_path, role="nurse")

    assert counts["N1"] == Decimal("2")
    assert counts["N2"] == Decimal("2")
    assert "N3" not in counts
