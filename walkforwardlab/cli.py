from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import LabError, load_bars, parse_config
from .engine import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="walkforwardlab", description="Leakage-resistant historical walk-forward measurement")
    parser.add_argument("config"); parser.add_argument("bars"); parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        config = parse_config(json.loads(Path(args.config).read_text(encoding="utf-8")))
        report = run(config, load_bars(args.bars))
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output: Path(args.output).write_text(rendered, encoding="utf-8")
        else: print(rendered, end="")
    except (OSError, json.JSONDecodeError, LabError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
    return 0
