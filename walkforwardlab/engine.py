"""Causal fold construction, training-only selection, and test measurement."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from itertools import product
from typing import Any

from .core import Bar, Config, LabError


def fmt(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000000000001")), "f").rstrip("0").rstrip(".") or "0"


def position(bars: list[Bar], index: int, lookback: int, threshold: Decimal, mode: str) -> int:
    change = bars[index].close / bars[index - lookback].close - 1
    raw = 1 if change > threshold else -1 if change < -threshold else 0
    return raw if mode == "momentum" else -raw


def measure(bars: list[Bar], indices: range, lookback: int, threshold: Decimal, mode: str, cost_bps: Decimal) -> dict[str, Any]:
    factor = Decimal(1); peak = Decimal(1); max_drawdown = Decimal(0); previous = 0; turnover = Decimal(0); trades = 0
    for index in indices:
        current = position(bars, index, lookback, threshold, mode)
        change = abs(current - previous); turnover += change
        if change: trades += 1
        gross = Decimal(current) * (bars[index + 1].close / bars[index].close - 1)
        net = gross - Decimal(change) * cost_bps / Decimal(10000)
        factor *= 1 + net
        if factor <= 0: raise LabError("cost-adjusted equity became non-positive")
        peak = max(peak, factor); max_drawdown = max(max_drawdown, (peak - factor) / peak)
        previous = current
    return {"return": fmt(factor - 1), "max_drawdown": fmt(max_drawdown), "turnover_units": fmt(turnover), "trade_events": trades, "observations": len(indices)}


def run(config: Config, bars: list[Bar]) -> dict[str, Any]:
    max_lookback = max(config.lookbacks)
    first_test = config.train_size + config.embargo_size
    if config.train_size <= max_lookback or first_test + config.test_size >= len(bars):
        raise LabError("not enough bars for one complete fold and next-bar returns")
    folds = []; test_start = first_test; fold_id = 0
    while test_start + config.test_size < len(bars):
        train_end = test_start - config.embargo_size
        train_start = max_lookback
        train_indices = range(train_start, train_end)
        candidates = []
        for mode, lookback, threshold in product(config.modes, config.lookbacks, config.thresholds):
            metrics = measure(bars, train_indices, lookback, threshold, mode, config.cost_bps)
            candidates.append((Decimal(metrics["return"]), -Decimal(metrics["max_drawdown"]), mode, -lookback, -threshold, metrics))
        chosen = max(candidates)
        _, _, mode, neg_lookback, neg_threshold, train_metrics = chosen
        lookback, threshold = -neg_lookback, -neg_threshold
        test_indices = range(test_start, test_start + config.test_size)
        test_metrics = measure(bars, test_indices, lookback, threshold, mode, config.cost_bps)
        folds.append({
            "fold": fold_id,
            "train": {"start": bars[train_start].timestamp, "end": bars[train_end - 1].timestamp, "observations": len(train_indices)},
            "embargo": {"bars": config.embargo_size, "start_index": train_end, "end_index_exclusive": test_start},
            "test": {"start": bars[test_start].timestamp, "end": bars[test_start + config.test_size - 1].timestamp, **test_metrics},
            "selected_on_train_only": {"mode": mode, "lookback": lookback, "threshold": fmt(threshold), "metrics": train_metrics},
        })
        fold_id += 1; test_start += config.step_size
    if not folds: raise LabError("no complete folds")
    combined = Decimal(1)
    for fold in folds: combined *= 1 + Decimal(fold["test"]["return"])
    report = {"schema":"walkforwardlab/report-1", "folds":folds, "aggregate":{"fold_count":len(folds), "compounded_test_return":fmt(combined-1)}, "claims":"historical_measurement_only"}
    report["report_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return report
