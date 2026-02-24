from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional


def normalize_item_name(name: str) -> str:
    if name is None:
        return ""
    text = str(name).strip()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[（(][^）)]*[）)]", "", text)
    return text


def extract_period_tag(name: str) -> Optional[str]:
    if not name:
        return None
    match = re.search(r"[（(]([^）)]*)[）)]", str(name))
    if not match:
        return None
    return match.group(1)


def to_decimal(value, default=Decimal("0")) -> Decimal:
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def round_money(value: Decimal) -> Decimal:
    return to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def allocate_by_weight(total: Decimal, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    total = Decimal(total)
    if not weights:
        return {}
    weight_sum = sum(weights.values())
    if weight_sum == 0:
        return {k: Decimal("0.00") for k in weights}

    raw = {k: (total * w / weight_sum) for k, w in weights.items()}
    rounded = {k: round_money(v) for k, v in raw.items()}
    delta = total - sum(rounded.values())
    if delta != 0:
        max_key = max(weights, key=lambda k: weights[k])
        rounded[max_key] = round_money(rounded[max_key] + delta)
    return rounded


def is_lab_category(category: str) -> bool:
    if not category:
        return False
    return "化验" in str(category) or "检验" in str(category)


def detect_role_type(role: str) -> str:
    text = str(role or "")
    if "护士" in text or "护理" in text:
        return "nurse"
    return "doctor"


def role_flags(role: str) -> tuple[bool, bool, bool]:
    text = str(role or "")
    is_director = "科主任" in text
    is_deputy = "副主任" in text
    is_head_nurse = "护士长" in text
    return is_director, is_deputy, is_head_nurse

