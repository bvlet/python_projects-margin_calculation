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

        discount = None if discount_pct is None else (discount_pct / 100.0)
        margin = None if target_margin_pct is None else (target_margin_pct / 100.0)

        discount_assumed = False
        discount_solved = False
        av_assumed_zero = False

        if added_value is not None and added_value < 0:
            raise ValueError("Added Value cannot be negative.")

        if discount is not None and (discount < 0 or discount > 1):
            raise ValueError("Discount must be between 0% and 100%.")
        if margin is not None and (margin < 0 or margin > 1):
            raise ValueError("Target margin must be between 0% and 100%.")

        if (
            margin is not None
            and updated_sources.get("net2") == "user"
            and updated_sources.get("net1") == "user"
            and net1 is not None
            and net2 == net1
        ):
            updated_sources["net2"] = "calc"

        if margin is not None and sources.get("net2") != "user":
            net2 = None

        if (
            margin is not None
            and cost is not None
            and net2 is not None
            and sources.get("net2") == "user"
        ):
            raise ValueError("Too many inputs. Clear one of the fields to solve.")

        if added_value is None and discount is None:
            added_value = 0.0
            av_assumed_zero = True
            if net1 is None or net2 is None:
                discount = 0.0
                discount_assumed = True
        elif added_value is None:
            if not (net1 is not None and net2 is not None and discount is not None):
                added_value = 0.0
                av_assumed_zero = True
        elif discount is None:
            if margin is None or cost is None:
                if not (net1 is not None and net2 is not None and added_value is not None):
                    discount = 0.0
                    discount_assumed = True

        for _ in range(30):
            progress = False

            if added_value is None and net1 is not None and net2 is not None and discount is None:
                added_value = 0.0
                av_assumed_zero = True
                progress = True

            if margin is not None:
                if net2 is None and cost is not None:
                    if (1.0 - margin) == 0:
                        raise ValueError("Target margin cannot be 100% when solving Net2.")
                    net2 = cost / (1.0 - margin)
                    progress = True
                if cost is None and net2 is not None:
                    cost = net2 * (1.0 - margin)
                    progress = True

            if discount is None and (net2 is not None) and (net1 is not None) and (added_value is not None):
                denom = (net1 + added_value)
                if denom == 0:
                    raise ValueError("Net1 + Added Value cannot be 0 when solving discount.")

                discount_candidate = 1.0 - (net2 / denom)

                if discount_candidate < 0 and av_assumed_zero and updated_sources.get("added_value", "") != "user":
                    discount = 0.0
                    discount_solved = True
                    av_candidate = net2 - net1
                    if av_candidate < 0:
                        raise ValueError("Added Value cannot be negative with these inputs.")
                    added_value = av_candidate
                    progress = True
                else:
                    discount = discount_candidate
                    if discount < 0 or discount > 1:
                        raise ValueError("Solved discount is outside 0%..100%. Check inputs.")
                    discount_solved = True
                    progress = True

            if net2 is None and (net1 is not None) and (added_value is not None) and (discount is not None):
                net2 = (net1 + added_value) * (1.0 - discount)
                progress = True

            if net1 is None and (net2 is not None) and (added_value is not None) and (discount is not None):
                if (1.0 - discount) == 0:
                    raise ValueError("Discount cannot be 100% when solving Net1 from Net2.")
                net1 = (net2 / (1.0 - discount)) - added_value
                progress = True

            if added_value is None and (net2 is not None) and (net1 is not None) and (discount is not None):
                if (1.0 - discount) == 0:
                    raise ValueError("Discount cannot be 100% when solving Added Value.")
                av_candidate = (net2 / (1.0 - discount)) - net1
                if av_candidate < 0:
                    raise ValueError("Added Value cannot be negative with these inputs.")
                added_value = av_candidate
                progress = True

            if discount is None and discount_pct is None:
                if margin is None or cost is None:
                    if (
                        (net2 is None and net1 is not None and added_value is not None)
                        or (net1 is None and net2 is not None and added_value is not None)
                        or (added_value is None and net2 is not None and net1 is not None)
                    ):
                        discount = 0.0
                        discount_assumed = True
                        progress = True

            if not progress:
                break

        if cost is not None:
            if updated_sources.get("cost", "") == "user":
                updated_values["cost"] = fmt_money(cost)
            else:
                _set_calc_value(updated_values, updated_sources, "cost", fmt_money(cost))

        if net1 is not None:
            if updated_sources.get("net1", "") == "user":
                updated_values["net1"] = fmt_money(net1)
            else:
                _set_calc_value(updated_values, updated_sources, "net1", fmt_money(net1))

        if added_value is not None:
            if added_value < 0:
                raise ValueError("Added Value cannot be negative.")
            if updated_sources.get("added_value", "") == "user":
                updated_values["added_value"] = fmt_money(added_value)
            else:
                _set_calc_value(updated_values, updated_sources, "added_value", fmt_money(added_value))

        if discount is not None and (discount_pct is not None or discount_assumed or discount_solved):
            if updated_sources.get("discount", "") == "user":
                updated_values["discount"] = fmt_pct(discount * 100.0)
            else:
                _set_calc_value(updated_values, updated_sources, "discount", fmt_pct(discount * 100.0))

        if net2 is not None:
            if updated_sources.get("net2", "") == "user":
                updated_values["net2"] = fmt_money(net2)
            else:
                _set_calc_value(updated_values, updated_sources, "net2", fmt_money(net2))

        if cost is not None and net1 is not None and net1 != 0:
            margin_no_discount = ((net1 - cost) / net1) * 100.0
            _set_calc_value(updated_values, updated_sources, "m_no", fmt_pct(margin_no_discount))
        else:
            _set_calc_value(updated_values, updated_sources, "m_no", "—")

        if cost is not None and net2 is not None and net2 != 0:
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
