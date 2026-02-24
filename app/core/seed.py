from sqlalchemy import select

from app.core.config import DEFAULT_RULE_SET_CODE
from app.models.models import RuleSet, RuleParam, DictItemMapping, DictItemBehavior


DEFAULT_RULE_PARAMS = [
    ("lab_doctor_ratio", "0.7"),
    ("lab_nurse_ratio", "0.3"),
    ("lead_reading_director_ratio", "0.8"),
    ("lead_reading_deputy_ratio", "0"),
    ("lead_reading_head_nurse_ratio", "0.2"),
    ("bed_subsidy_doctor_ratio", "0.6666666667"),
    ("bed_subsidy_nurse_ratio", "0.3333333333"),
    ("head_nurse_score_coeff", "1.4"),
    ("doctor_pool_min_weight", "0.8"),
    ("surplus_director_ratio", "0.15"),
    ("surplus_head_nurse_ratio", "0.05"),
    ("admission_cert_unit", "50"),
]

DEFAULT_ITEM_MAPPINGS = [
    ("科主任判读费", "LEAD_READING_FEE", 10),
    ("判读费", "READING_FEE", 20),
    ("医师夜班", "DOC_NIGHT_FEE", 30),
    ("护理组夜班", "NUR_NIGHT_FEE", 30),
    ("科室盈余", "SURPLUS", 30),
    ("中医特色护理", "TCM_NURSING", 30),
    ("体检中心分配", "CHECKUP_CENTER_ALLOC", 30),
    ("床补", "BED_SUBSIDY", 30),
    ("护补", "NUR_SUBSIDY", 30),
    ("工作量", "WORKLOAD_MANUAL_PAY", 30),
    ("住院证补贴", "ADMISSION_CERT_FEE", 30),
    ("抽血费", "BLOOD_DRAW_FEE", 30),
    ("进修产假补贴", "STUDY_LEAVE_SUBSIDY", 30),
    ("胰岛素泵", "INSULIN_PUMP", 30),
    ("分摊综合手术室成本", "OR_COST_ALLOC", 30),
]

DEFAULT_ITEM_BEHAVIORS = [
    ("DOC_NIGHT_FEE", "DIRECT"),
    ("NUR_NIGHT_FEE", "DIRECT"),
    ("SURPLUS", "SPECIAL"),
    ("TCM_NURSING", "POOL_NURSING"),
    ("CHECKUP_CENTER_ALLOC", "POOL_DOCTOR"),
    ("READING_FEE", "SPECIAL"),
    ("LEAD_READING_FEE", "SPECIAL"),
    ("BED_SUBSIDY", "SPECIAL"),
    ("NUR_SUBSIDY", "POOL_NURSING"),
    ("WORKLOAD_MANUAL_PAY", "DIRECT"),
    ("ADMISSION_CERT_FEE", "DIRECT"),
    ("BLOOD_DRAW_FEE", "DIRECT"),
    ("STUDY_LEAVE_SUBSIDY", "DIRECT"),
    ("INSULIN_PUMP", "POOL_DOCTOR"),
    ("OR_COST_ALLOC", "RECON_ONLY"),
    ("UNCLASSIFIED_ITEM", "UNCLASSIFIED"),
]


def seed_defaults(session):
    rule_set = session.execute(
        select(RuleSet).where(RuleSet.code == DEFAULT_RULE_SET_CODE)
    ).scalar_one_or_none()
    if rule_set is None:
        rule_set = RuleSet(
            code=DEFAULT_RULE_SET_CODE,
            name="Default Rule Set",
            version="default",
            is_active=True,
        )
        session.add(rule_set)
        session.flush()

    existing_params = {
        p.param_key
        for p in session.execute(
            select(RuleParam).where(RuleParam.rule_set_id == rule_set.id)
        ).scalars()
    }
    for key, value in DEFAULT_RULE_PARAMS:
        if key in existing_params:
            continue
        session.add(
            RuleParam(
                rule_set_id=rule_set.id,
                param_key=key,
                param_value=str(value),
                param_value_num=float(value),
            )
        )

    existing_map = {
        (m.raw_item_name, m.item_code)
        for m in session.execute(select(DictItemMapping)).scalars()
    }
    for raw_name, item_code, priority in DEFAULT_ITEM_MAPPINGS:
        if (raw_name, item_code) in existing_map:
            continue
        session.add(
            DictItemMapping(
                raw_item_name=raw_name,
                item_code=item_code,
                priority=priority,
                is_active=True,
            )
        )

    existing_behavior = {
        b.item_code for b in session.execute(select(DictItemBehavior)).scalars()
    }
    for item_code, behavior in DEFAULT_ITEM_BEHAVIORS:
        if item_code in existing_behavior:
            continue
        session.add(DictItemBehavior(item_code=item_code, behavior_type=behavior))

    session.commit()
