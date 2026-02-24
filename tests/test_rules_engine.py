import asyncio
import io

from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.calc.engine import calculate_run
from app.core.db import Base
from app.models.models import (
    FactPayDetail,
    FactPaySummary,
    FactPool,
    FactPoolAlloc,
    QcIssue,
    RawDoctorWorkload,
    RawHospitalPerfItem,
    RawManualDoctorWorkloadPay,
    RawManualEntry,
    RawNightShift,
    RawNurseWorkload,
    RawReadingFee,
    RawRoster,
    ReconcileItem,
    RuleParam,
    RuleSet,
    RunBatch,
)


def make_session():
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def create_run(session):
    run = RunBatch(month="2025-12", dept_name="TEST", rule_version="default")
    session.add(run)
    session.commit()
    return run.id


def test_night_split_counts():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawRoster(run_id=run_id, name="N1", role="护士", perf_score=1),
            RawNightShift(run_id=run_id, name="D1", night_count=2),
            RawNightShift(run_id=run_id, name="N1", night_count=2),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="医师夜班(12月)",
                item_name_norm="医师夜班",
                period_tag="12月",
                amount=100,
            ),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="护理组夜班(12月)",
                item_name_norm="护理组夜班",
                period_tag="12月",
                amount=100,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    rows = session.execute(select(FactPayDetail)).scalars().all()
    doc = next(r for r in rows if r.item_code == "DOC_NIGHT_FEE")
    nur = next(r for r in rows if r.item_code == "NUR_NIGHT_FEE")
    assert float(doc.amount) == 100.0
    assert float(nur.amount) == 100.0


def test_night_split_ignores_night_unit_params():
    session = make_session()
    run_id = create_run(session)
    custom_rule = RuleSet(code="custom", name="custom", version="1", is_active=True)
    session.add(custom_rule)
    session.flush()
    session.add(
        RuleParam(
            rule_set_id=custom_rule.id,
            param_key="doctor_night_unit",
            param_value="999",
            param_value_num=999,
        )
    )
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawRoster(run_id=run_id, name="D2", role="医师", perf_score=1),
            RawNightShift(run_id=run_id, name="D1", night_count=2),
            RawNightShift(run_id=run_id, name="D2", night_count=1),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="医师夜班(12月)",
                item_name_norm="医师夜班",
                period_tag="12月",
                amount=90,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    rows = [
        r
        for r in session.execute(select(FactPayDetail)).scalars().all()
        if r.item_code == "DOC_NIGHT_FEE"
    ]
    amounts = {r.name: float(r.amount) for r in rows}
    assert round(amounts["D1"], 2) == 60.0
    assert round(amounts["D2"], 2) == 30.0


def test_reading_fee_lab_split():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="判读费(12月)",
                item_name_norm="判读费",
                period_tag="12月",
                amount=100,
            ),
            RawReadingFee(run_id=run_id, category="化验", name="D1", amount=100),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    direct = session.execute(select(FactPayDetail)).scalars().all()
    pool = session.execute(select(FactPool)).scalars().all()
    doc_amount = sum(float(r.amount) for r in direct if r.item_code == "READING_FEE")
    pool_amount = sum(float(r.amount) for r in pool if r.source_item_code == "READING_FEE")
    assert doc_amount == 70.0
    assert pool_amount == 30.0


def test_bed_subsidy_split():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawRoster(run_id=run_id, name="D2", role="医师", perf_score=1),
            RawDoctorWorkload(run_id=run_id, name="D1", workload=1, bed_days=10, admission_cert_count=0),
            RawDoctorWorkload(run_id=run_id, name="D2", workload=1, bed_days=20, admission_cert_count=0),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="床补(12月)",
                item_name_norm="床补",
                period_tag="12月",
                amount=300,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    pool = session.execute(select(FactPool)).scalars().all()
    pool_amount = sum(float(r.amount) for r in pool if r.source_item_code == "BED_SUBSIDY")
    details = [r for r in session.execute(select(FactPayDetail)).scalars() if r.item_code == "BED_SUBSIDY"]
    total_direct = sum(float(r.amount) for r in details)
    assert pool_amount == 100.0
    assert round(total_direct, 2) == 200.0


def test_nursing_pool_head_nurse_weight():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="H1", role="护士长", perf_score=1),
            RawRoster(run_id=run_id, name="N1", role="护理", perf_score=1),
            RawNurseWorkload(run_id=run_id, name="H1", score=0, blood_draw_count=0),
            RawNurseWorkload(run_id=run_id, name="N1", score=4, blood_draw_count=0),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="护补(12月)",
                item_name_norm="护补",
                period_tag="12月",
                amount=100,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    allocs = session.execute(select(FactPoolAlloc)).scalars().all()
    head = next(a for a in allocs if a.name == "H1")
    nurse = next(a for a in allocs if a.name == "N1")
    assert round(float(head.amount), 2) == 58.33
    assert round(float(nurse.amount), 2) == 41.67


def test_doctor_pool_min_weight():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawRoster(run_id=run_id, name="D2", role="医师", perf_score=1),
            RawDoctorWorkload(run_id=run_id, name="D1", workload=10, bed_days=0, admission_cert_count=0),
            RawDoctorWorkload(run_id=run_id, name="D2", workload=0, bed_days=0, admission_cert_count=0),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="胰岛素泵(12月)",
                item_name_norm="胰岛素泵",
                period_tag="12月",
                amount=100,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    allocs = session.execute(select(FactPoolAlloc)).scalars().all()
    d1 = next(a for a in allocs if a.name == "D1")
    d2 = next(a for a in allocs if a.name == "D2")
    assert round(float(d1.amount), 2) == 92.59
    assert round(float(d2.amount), 2) == 7.41


def test_surplus_distribution():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="主任", role="科主任", perf_score=10),
            RawRoster(run_id=run_id, name="护士长", role="护士长", perf_score=8),
            RawRoster(run_id=run_id, name="医师", role="医师", perf_score=6),
            RawRoster(run_id=run_id, name="赵医师", role="医师", perf_score=4),
            RawRoster(run_id=run_id, name="刘护士", role="护理", perf_score=5),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="科室盈余(12月)",
                item_name_norm="科室盈余",
                period_tag="12月",
                amount=1000,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    summary = {r.name: r for r in session.execute(select(FactPaySummary)).scalars()}
    assert round(float(summary["主任"].surplus), 2) == 392.43
    assert round(float(summary["护士长"].surplus), 2) == 243.94
    assert round(float(summary["医师"].surplus), 2) == 145.45


def test_or_cost_recon_only():
    session = make_session()
    run_id = create_run(session)
    session.add(
        RawHospitalPerfItem(
            run_id=run_id,
            item_name="分摊综合手术室成本(12月)",
            item_name_norm="分摊综合手术室成本",
            period_tag="12月",
            amount=500,
        )
    )
    session.commit()

    calculate_run(session, run_id)

    recon = session.execute(select(ReconcileItem)).scalars().all()
    item = next(r for r in recon if r.item_code == "OR_COST_ALLOC")
    assert float(item.allocated_amount) == 0.0
    assert float(item.delta) == 500.0


def test_admission_cert_reconcile_note():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawDoctorWorkload(run_id=run_id, name="D1", workload=1, bed_days=1, admission_cert_count=2),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="住院证补贴(12月)",
                item_name_norm="住院证补贴",
                period_tag="12月",
                amount=200,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    recon = session.execute(select(ReconcileItem)).scalars().all()
    item = next(r for r in recon if r.item_code == "ADMISSION_CERT_FEE")
    assert item.note == "Admission cert residual"
    assert float(item.delta) == 100.0


def test_manual_entry_item_name_uses_mapping_table():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="工作量(12月)",
                item_name_norm="工作量",
                period_tag="12月",
                amount=1000,
            ),
            # Manual entry item name is not the enum "WORKLOAD", but should still map to WORKLOAD_MANUAL_PAY
            RawManualEntry(
                run_id=run_id,
                target_type="PERSON",
                target_value="D1",
                item_type="工作量（手工录入）",
                amount=1000,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    recon = session.execute(select(ReconcileItem)).scalars().all()
    workload = [r for r in recon if r.item_code == "WORKLOAD_MANUAL_PAY"]
    assert len(workload) == 1
    assert float(workload[0].source_amount) == 1000.0
    assert float(workload[0].allocated_amount) == 1000.0
    assert float(workload[0].delta) == 0.0
    assert not any(str(r.item_code).startswith("RAW_ITEM_") for r in recon)


def test_export_excel_has_sheets():
    from app.api.routes.runs import export_excel
    from fastapi.responses import StreamingResponse
    import openpyxl

    session = make_session()
    run_id = create_run(session)
    session.add(
        RawHospitalPerfItem(
            run_id=run_id,
            item_name="科室盈余(12月)",
            item_name_norm="科室盈余",
            period_tag="12月",
            amount=0,
        )
    )
    session.commit()
    calculate_run(session, run_id)

    response = export_excel(run_id, db=session)
    assert isinstance(response, StreamingResponse)
    async def _collect(resp):
        chunks = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk)
        return b"".join(chunks)

    content = asyncio.run(_collect(response))
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    assert wb.sheetnames == ["汇总", "明细", "对账", "异常"]


def test_export_pdf_returns_pdf_bytes(monkeypatch):
    from app.api.routes import runs as runs_routes
    from fastapi.responses import StreamingResponse

    def _fake_render_pdf_from_html(*, html, params):
        assert "<html" in html.lower()
        return b"%PDF-1.4\n%fake\n"

    import app.reporting.pdf_renderer as pdf_renderer

    monkeypatch.setattr(pdf_renderer, "render_pdf_from_html", _fake_render_pdf_from_html)

    session = make_session()
    run_id = create_run(session)
    session.add(
        RawHospitalPerfItem(
            run_id=run_id,
            item_name="科室盈余(12月)",
            item_name_norm="科室盈余",
            period_tag="12月",
            amount=0,
        )
    )
    session.commit()
    calculate_run(session, run_id)

    response = runs_routes.export_pdf(run_id, db=session)
    assert isinstance(response, StreamingResponse)

    async def _collect(resp):
        chunks = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk)
        return b"".join(chunks)

    content = asyncio.run(_collect(response))
    assert content.startswith(b"%PDF")


def test_divide_by_zero_qc():
    session = make_session()
    run_id = create_run(session)
    session.add_all(
        [
            RawRoster(run_id=run_id, name="D1", role="医师", perf_score=1),
            RawDoctorWorkload(run_id=run_id, name="D1", workload=1, bed_days=0, admission_cert_count=0),
            RawHospitalPerfItem(
                run_id=run_id,
                item_name="床补(12月)",
                item_name_norm="床补",
                period_tag="12月",
                amount=100,
            ),
        ]
    )
    session.commit()

    calculate_run(session, run_id)

    issues = session.execute(select(QcIssue)).scalars().all()
    assert any(i.issue_type == "DIVIDE_BY_ZERO" for i in issues)
