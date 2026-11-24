"""Offline research loop and one-shot holdout command."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .core import Costs, evaluate, load_bars
from .snapshot import capture


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, value: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, sort_keys=True) + "\n")


def candidate_source(lookback: int, top_n: int) -> str:
    return ("\"\"\"Generated candidate; never edit the evaluator.\"\"\"\n"
            f"LOOKBACK = {lookback}\nTOP_N = {top_n}\n"
            "def hypothesis():\n"
            "    return f'Rank {LOOKBACK}-session momentum; hold top {TOP_N}'\n")


def candidate_parameters(source: str) -> tuple[int, int]:
    """Read only literal strategy constants from generated code, without executing it."""
    assignments = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {"LOOKBACK", "TOP_N"}:
                assignments[target.id] = ast.literal_eval(node.value)
    lookback, top_n = assignments["LOOKBACK"], assignments["TOP_N"]
    if type(lookback) is not int or type(top_n) is not int:
        raise ValueError("candidate parameters must be integers")
    return lookback, top_n


def research(args: argparse.Namespace) -> None:
    bars, fingerprint = load_bars(args.csv)
    out = Path(args.out)
    if out.exists():
        raise ValueError("run directory already exists; choose a fresh path")
    train_end = date.fromisoformat(args.train_end)
    valid_end = date.fromisoformat(args.valid_end)
    test_end = date.fromisoformat(args.test_end)
    first = bars[0].day
    if not first < train_end < valid_end < test_end <= bars[-1].day:
        raise ValueError("ordered train, validation and test dates must fall within the dataset")
    train_start = first
    valid_start = train_end.fromordinal(train_end.toordinal() + 1)
    test_start = valid_end.fromordinal(valid_end.toordinal() + 1)
    costs = Costs()
    out.mkdir(parents=True)
    (out / "candidates").mkdir()
    config = {
        "data_sha256": fingerprint, "source": str(Path(args.csv).resolve()),
        "train_start": train_start.isoformat(), "train_end": args.train_end,
        "valid_start": valid_start.isoformat(), "valid_end": args.valid_end,
        "test_start": test_start.isoformat(), "test_end": args.test_end,
        "costs": asdict(costs), "max_trials": args.max_trials,
        "max_seconds": args.max_seconds, "engine": "deterministic-template-v1",
    }
    write_json(out / "config.json", config)
    started = time.monotonic()
    best = None
    proposals = [(l, n) for l in (5, 10, 20, 40, 60) for n in (1, 2, 3)]
    for index, (lookback, top_n) in enumerate(proposals[:args.max_trials], 1):
        if time.monotonic() - started >= args.max_seconds:
            break
        source = candidate_source(lookback, top_n)
        candidate = out / "candidates" / f"trial_{index:03d}.py"
        candidate.write_text(source, encoding="utf-8")
        record = {
            "trial": index, "hypothesis": f"{lookback}-session momentum; top {top_n}",
            "candidate": str(candidate.relative_to(out)),
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "status": "failed", "train": None, "validation": None,
        }
        try:
            lookback, top_n = candidate_parameters(candidate.read_text())
            train = evaluate(bars, train_start, train_end, lookback, top_n, costs)
            valid = evaluate(bars, valid_start, valid_end, lookback, top_n, costs)
            record.update(status="completed", train=train, validation=valid)
            score = valid["total_return"]
            if best is None or score > best["validation"]["total_return"]:
                best = record
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        append_jsonl(out / "experiments.jsonl", record)
    log_path = out / "experiments.jsonl"
    count = len(log_path.read_text().splitlines()) if log_path.exists() else 0
    write_json(out / "summary.json", {
        "trials_recorded": count,
        "selected_trial": best["trial"] if best else None,
        "selection_metric": "validation_total_return",
        "holdout_opened": False,
    })
    print(out.resolve())


def test_holdout(args: argparse.Namespace) -> None:
    out = Path(args.run)
    if (out / "holdout.json").exists() or (out / ".holdout-opened").exists():
        raise ValueError("holdout has already been opened for this run")
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    if summary["selected_trial"] is None:
        raise ValueError("no completed candidate to test")
    bars, fingerprint = load_bars(args.csv)
    if fingerprint != config["data_sha256"]:
        raise ValueError("input data fingerprint differs from research run")
    selected = None
    for line in (out / "experiments.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record["trial"] == summary["selected_trial"]:
            selected = record
            break
    if selected is None:
        raise ValueError("selected trial missing from experiment log")
    source = (out / selected["candidate"]).read_text()
    if hashlib.sha256(source.encode()).hexdigest() != selected["source_sha256"]:
        raise ValueError("selected candidate was modified")
    lookback, top_n = candidate_parameters(source)
    (out / ".holdout-opened").write_text("opened\n")
    try:
        result = evaluate(
            bars, date.fromisoformat(config["test_start"]),
            date.fromisoformat(config["test_end"]), lookback, top_n,
            Costs(**config["costs"]),
        )
        write_json(out / "holdout.json", {
            "trial": selected["trial"], "status": "completed", "metrics": result,
        })
    except Exception as exc:
        write_json(out / "holdout.json", {
            "trial": selected["trial"], "status": "failed", "error": str(exc),
        })
        raise
    summary["holdout_opened"] = True
    write_json(out / "summary.json", summary)
    print((out / "holdout.json").resolve())


def main() -> None:
    parser = argparse.ArgumentParser(prog="twquant")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("csv")
    run = sub.add_parser("research")
    run.add_argument("csv")
    run.add_argument("--train-end", required=True)
    run.add_argument("--valid-end", required=True)
    run.add_argument("--test-end", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--max-trials", type=int, default=12)
    run.add_argument("--max-seconds", type=int, default=120)
    holdout = sub.add_parser("test")
    holdout.add_argument("csv")
    holdout.add_argument("--run", required=True)
    snapshot = sub.add_parser("snapshot", help="capture an observed public daily quote response")
    snapshot.add_argument("market", choices=("twse", "tpex"))
    snapshot.add_argument("--out", default="data/raw")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            bars, fingerprint = load_bars(args.csv)
            print(json.dumps({"rows": len(bars), "sha256": fingerprint}))
        elif args.command == "research":
            if not 1 <= args.max_trials <= 15 or not 1 <= args.max_seconds <= 3600:
                raise ValueError("max-trials must be 1..15 and max-seconds 1..3600")
            research(args)
        elif args.command == "test":
            test_holdout(args)
        else:
            raw, manifest = capture(args.market, Path(args.out))
            print(json.dumps({"raw": str(raw.resolve()), "manifest": str(manifest.resolve())}))
    except (ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
