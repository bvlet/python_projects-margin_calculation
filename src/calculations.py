from dataclasses import dataclass
from typing import Dict, Optional, Tuple


def parse_float(value: str) -> Optional[float]:
    raw = (value or "").strip()
    if not raw:
        return None
    return float(raw.replace(",", "."))


def fmt_money(value: float) -> str:
    return f"{value:.2f}"


def fmt_pct(value: float) -> str:
    return f"{value:.2f}"


@dataclass
class CalculationResult:
    values: Dict[str, str]
    sources: Dict[str, str]
    status: str


FIELD_NAMES = (
    "cost",
    "net1",
    "added_value",
    "discount",
    "net2",
    "target_margin",
    "m_no",
    "m_with",
    "status",
)


def _set_calc_value(values: Dict[str, str], sources: Dict[str, str], name: str, value: str) -> None:
    values[name] = value
    sources[name] = "calc"


def calculate_all(values: Dict[str, str], sources: Dict[str, str]) -> CalculationResult:
    updated_values = dict(values)
    updated_sources = dict(sources)

    _set_calc_value(updated_values, updated_sources, "m_no", "")
    _set_calc_value(updated_values, updated_sources, "m_with", "")
    _set_calc_value(updated_values, updated_sources, "status", "")

    try:
        cost = parse_float(updated_values.get("cost", ""))
        net1 = parse_float(updated_values.get("net1", ""))
        added_value = parse_float(updated_values.get("added_value", ""))
        discount_pct = parse_float(updated_values.get("discount", ""))
        net2 = parse_float(updated_values.get("net2", ""))
        target_margin_pct = parse_float(updated_values.get("target_margin", ""))

        if cost is None or net1 is None:
            raise ValueError("Cost Price and Net1 are required.")

        if target_margin_pct is not None and target_margin_pct < 0:
            raise ValueError("Target margin cannot be negative.")

        added_value = 0.0 if added_value is None else added_value
        discount = 0.0 if discount_pct is None else (discount_pct / 100.0)
        margin = None if target_margin_pct is None else (target_margin_pct / 100.0)

        denom = net1 + added_value
        if margin is not None:
            net2 = cost * (1.0 + margin)
            if denom == 0:
                raise ValueError("Net1 + Added Value cannot be 0 when solving discount.")
            discount = 1.0 - (net2 / denom)
            updated_sources["net2"] = "calc"
            updated_sources["discount"] = "calc"
        elif net2 is not None:
            if denom == 0:
                raise ValueError("Net1 + Added Value cannot be 0 when solving discount.")
            discount = 1.0 - (net2 / denom)
            updated_sources["discount"] = "calc"
            if updated_sources.get("net2", "") != "user":
                updated_sources["net2"] = "calc"
        else:
            net2 = (net1 + added_value) * (1.0 - discount)
            updated_sources["net2"] = "calc"
            if updated_sources.get("discount", "") != "user":
                updated_sources["discount"] = "calc"

        if updated_sources.get("cost", "") == "user":
            updated_values["cost"] = fmt_money(cost)
        else:
            _set_calc_value(updated_values, updated_sources, "cost", fmt_money(cost))

        if updated_sources.get("net1", "") == "user":
            updated_values["net1"] = fmt_money(net1)
        else:
            _set_calc_value(updated_values, updated_sources, "net1", fmt_money(net1))

        if updated_sources.get("added_value", "") == "user":
            updated_values["added_value"] = fmt_money(added_value)
        else:
            _set_calc_value(updated_values, updated_sources, "added_value", fmt_money(added_value))

        if updated_sources.get("discount", "") == "user":
            updated_values["discount"] = fmt_pct(discount * 100.0)
        else:
            _set_calc_value(updated_values, updated_sources, "discount", fmt_pct(discount * 100.0))

        if updated_sources.get("net2", "") == "user":
            updated_values["net2"] = fmt_money(net2)
        else:
            _set_calc_value(updated_values, updated_sources, "net2", fmt_money(net2))

        if net1 != 0:
            margin_no_discount = ((net1 - cost) / net1) * 100.0
            _set_calc_value(updated_values, updated_sources, "m_no", fmt_pct(margin_no_discount))
        else:
            _set_calc_value(updated_values, updated_sources, "m_no", "—")

        if net2 is not None and net2 != 0:
            margin_with_discount = ((net2 - cost) / net2) * 100.0
            _set_calc_value(updated_values, updated_sources, "m_with", fmt_pct(margin_with_discount))
        else:
            _set_calc_value(updated_values, updated_sources, "m_with", "—")

        _set_calc_value(updated_values, updated_sources, "status", "")

    except ValueError as exc:
        _set_calc_value(updated_values, updated_sources, "status", str(exc))

    return CalculationResult(updated_values, updated_sources, updated_values.get("status", ""))


def reset_values() -> Tuple[Dict[str, str], Dict[str, str]]:
    values = {name: "" for name in FIELD_NAMES}
    sources = {name: "" for name in FIELD_NAMES}
    return values, sources
