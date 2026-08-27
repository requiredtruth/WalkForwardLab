# WalkForwardLab

WalkForwardLab is a zero-dependency audit harness for a common failure mode: **parameter selection that quietly sees the test period**. It builds expanding historical folds, selects a tiny strategy grid on training data only, skips a visible embargo, freezes the selection, and measures the following non-overlapping window.

```sh
./install.sh
```

That command runs the tests, compiles every module, and processes bundled synthetic prices. It downloads nothing and needs no account or credential.

## Guarantees in 0.1.0

- CSV rows must be strictly increasing canonical UTC `timestamp,close` values.
- Momentum/reversion signals at bar *t* use only closes at or before *t*.
- The position applies to the return from *t* to *t+1*.
- Parameter selection uses only each fold's expanding training indices.
- Embargo indices are reported and excluded from both training and testing.
- Test windows cannot overlap (`step_size >= test_size`).
- Turnover costs are charged whenever the position changes, including reversals.
- Candidate tie-breaking is deterministic.

## Run the demonstration

```sh
./run.sh
python -m walkforwardlab walkforwardlab/data/demo_config.json \
  walkforwardlab/data/demo_bars.csv --output report.json
```

Stable errors anchor the actual problems:

```text
error: step_size must prevent overlapping test windows
error: timestamps must strictly increase
error: not enough bars for one complete fold and next-bar returns
```

## Distinction

Large backtesting frameworks focus on strategy implementation, portfolio simulation, and integrations. WalkForwardLab is deliberately smaller: it is a dependency-free leakage witness. Its report exposes the exact training, embargo, and test boundaries plus the training-only winning parameters for every fold. It is useful as a reproducible preflight check or benchmark fixture, not as an execution platform.

## Limitations

- 0.1.0 accepts close-only bars and two transparent toy signal families; this makes leakage inspection easy but is not realistic market modeling.
- Costs are turnover basis points. There is no spread, market impact, latency, borrow, funding, tax, capacity, or partial-fill model.
- Training selection can overfit even when test leakage is absent.
- Historical results are not forecasts, recommendations, or evidence of future profitability.
- Synthetic demonstration data proves behavior, not strategy quality.

## Support

Donations can fund more production and may request priority for a compatible measurement direction through the issue template with a public transaction hash. They do not guarantee implementation or buy support, ownership, returns, or preference. See [SUPPORT.md](SUPPORT.md) and verify the asset and network before sending.

Apache-2.0 licensed.


## Standard launcher

`./run.sh` is the normal entry point. It runs `./install.sh` automatically when setup is missing, then opens the PySide6 control panel with live output and actions for the demo, tests, repair, and stop. Use `./cli.sh` for CLI-only operation.
