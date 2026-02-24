from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calc.utils import round_money, to_decimal
from app.models.models import FactPaySummary, QcIssue, ReconcileItem, RunBatch


@dataclass(frozen=True)
class RunReportOptions:
    paper: str = "A4"
    orientation: str = "landscape"  # "portrait" | "landscape"
    sections: tuple[str, ...] = ("summary", "reconcile", "qc", "sign")


def _parse_sections(sections: str) -> tuple[str, ...]:
    parts = [p.strip().lower() for p in (sections or "").split(",")]
    parts = [p for p in parts if p]
    if not parts:
        return ("summary", "reconcile", "qc", "sign")
    return tuple(dict.fromkeys(parts))


def _money(value: Decimal | float | int | str | None) -> str:
    d = to_decimal(value, default=Decimal("0"))
    return f"{round_money(d):.2f}"


def build_run_report_context(
    *,
    db: Session,
    run_id: int,
    hospital_name: str,
    sections: Iterable[str],
) -> dict:
    run = db.get(RunBatch, run_id)
    if not run:
        raise KeyError("Run not found")

    month_text = ""
    if run.month:
        # "2025-12" -> "2025年12月"
        try:
            year, month = run.month.split("-", 1)
            month_text = f"{year}年{month}月"
        except ValueError:
            month_text = run.month

    want = set([s.lower() for s in sections])

    context: dict = {
        "hospital_name": hospital_name,
        "run": {"id": run.id, "month": run.month, "dept_name": run.dept_name},
        "month_text": month_text,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sections": sorted(list(want)),
        "summary_rows": [],
        "summary_totals": None,
        "reconcile_rows": [],
        "reconcile_totals": None,
        "qc_rows": [],
    }

    if "summary" in want:
        rows = db.execute(
            select(FactPaySummary).where(FactPaySummary.run_id == run_id).order_by(FactPaySummary.name)
        ).scalars().all()
        summary_rows = []
        totals = {
            "direct_total": Decimal("0"),
            "pool_nursing": Decimal("0"),
            "pool_doctor": Decimal("0"),
            "grand_total": Decimal("0"),
        }
        for r in rows:
            direct_total = to_decimal(r.direct_total)
            pool_nursing = to_decimal(r.pool_nursing)
            pool_doctor = to_decimal(r.pool_doctor)
            grand_total = to_decimal(r.grand_total)
            totals["direct_total"] += direct_total
            totals["pool_nursing"] += pool_nursing
            totals["pool_doctor"] += pool_doctor
            totals["grand_total"] += grand_total
            summary_rows.append(
                {
                    "name": r.name,
                    "role": r.role,
                    "direct_total": _money(direct_total),
                    "pool_nursing": _money(pool_nursing),
                    "pool_doctor": _money(pool_doctor),
                    "grand_total": _money(grand_total),
                }
            )
        context["summary_rows"] = summary_rows
        context["summary_totals"] = {**{k: _money(v) for k, v in totals.items()}, **{"count": len(summary_rows)}}

    if "reconcile" in want:
        rows = db.execute(
            select(ReconcileItem).where(ReconcileItem.run_id == run_id).order_by(ReconcileItem.item_code)
        ).scalars().all()
        reconcile_rows = []
        totals = {"source_amount": Decimal("0"), "allocated_amount": Decimal("0"), "delta": Decimal("0")}
        for r in rows:
            source_amount = to_decimal(r.source_amount)
            allocated_amount = to_decimal(r.allocated_amount)
            delta = to_decimal(r.delta)
            totals["source_amount"] += source_amount
            totals["allocated_amount"] += allocated_amount
            totals["delta"] += delta
            reconcile_rows.append(
                {
                    "item_code": r.item_code,
                    "source_amount": _money(source_amount),
                    "allocated_amount": _money(allocated_amount),
                    "delta": _money(delta),
                    "note": r.note or "",
                }
            )
        context["reconcile_rows"] = reconcile_rows
        context["reconcile_totals"] = {**{k: _money(v) for k, v in totals.items()}, **{"count": len(reconcile_rows)}}

    if "qc" in want:
        rows = db.execute(select(QcIssue).where(QcIssue.run_id == run_id)).scalars().all()
        qc_rows = []
        for r in rows:
            payload_str: Optional[str]
            if r.payload is None:
                payload_str = None
            else:
                try:
                    payload_str = json.dumps(r.payload, ensure_ascii=False, sort_keys=True)
                except TypeError:
                    payload_str = str(r.payload)
            qc_rows.append(
                {
                    "issue_type": r.issue_type,
                    "severity": r.severity,
                    "message": r.message,
                    "payload": payload_str,
                }
            )
        context["qc_rows"] = qc_rows

    return context


def render_run_report_html(*, context: dict, options: RunReportOptions) -> str:
    template_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("run_report.html")
    return template.render(**context, options=options)
