"""Strict data and configuration contracts."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class LabError(ValueError):
    pass


@dataclass(frozen=True)
class Bar:
    timestamp: str
    close: Decimal


@dataclass(frozen=True)
class Config:
    train_size: int
    test_size: int
    step_size: int
    embargo_size: int
    lookbacks: tuple[int, ...]
    thresholds: tuple[Decimal, ...]
    modes: tuple[str, ...]
    cost_bps: Decimal


def number(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise LabError(f"{label} must be a decimal string or integer")
    try: result = Decimal(str(value))
    except InvalidOperation as exc: raise LabError(f"{label} is not decimal") from exc
    if not result.is_finite(): raise LabError(f"{label} must be finite")
    return result


def parse_config(raw: Any) -> Config:
    expected = {"train_size", "test_size", "step_size", "embargo_size", "lookbacks", "thresholds", "modes", "cost_bps"}
    if not isinstance(raw, dict) or set(raw) != expected: raise LabError("config fields are incomplete or unexpected")
    for key in ["train_size", "test_size", "step_size", "embargo_size"]:
        if type(raw[key]) is not int or raw[key] < (0 if key == "embargo_size" else 1): raise LabError(f"{key} has an invalid bound")
    if raw["step_size"] < raw["test_size"]: raise LabError("step_size must prevent overlapping test windows")
    lookbacks = raw["lookbacks"]
    if not isinstance(lookbacks, list) or not lookbacks or lookbacks != sorted(set(lookbacks)) or any(type(x) is not int or x < 1 for x in lookbacks):
        raise LabError("lookbacks must be sorted unique positive integers")
    thresholds_raw = raw["thresholds"]
    thresholds = tuple(number(x, "threshold") for x in thresholds_raw) if isinstance(thresholds_raw, list) else ()
    if not thresholds or list(thresholds) != sorted(set(thresholds)) or any(x < 0 or x >= 1 for x in thresholds):
        raise LabError("thresholds must be sorted unique decimals from 0 through less than 1")
    modes = raw["modes"]
    if not isinstance(modes, list) or not modes or modes != sorted(set(modes)) or any(x not in {"momentum", "reversion"} for x in modes):
        raise LabError("modes must be sorted unique momentum/reversion values")
    cost = number(raw["cost_bps"], "cost_bps")
    if cost < 0 or cost > 1000: raise LabError("cost_bps must be from 0 to 1000")
    return Config(raw["train_size"], raw["test_size"], raw["step_size"], raw["embargo_size"], tuple(lookbacks), thresholds, tuple(modes), cost)


def load_bars(path: str) -> list[Bar]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["timestamp", "close"]: raise LabError("CSV header must be exactly timestamp,close")
        rows = list(reader)
    if not rows: raise LabError("CSV must contain bars")
    bars: list[Bar] = []; previous: datetime | None = None
    for row in rows:
        value = row["timestamp"]
        if not value.endswith("Z"): raise LabError("timestamps must be canonical UTC")
        try: current = datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc: raise LabError("timestamps must be ISO-8601 UTC") from exc
        if current.tzinfo != timezone.utc or current.isoformat().replace("+00:00", "Z") != value: raise LabError("timestamps must be canonical UTC")
        if previous is not None and current <= previous: raise LabError("timestamps must strictly increase")
        close = number(row["close"], "close")
        if close <= 0: raise LabError("close must be positive")
        bars.append(Bar(value, close)); previous = current
    return bars
