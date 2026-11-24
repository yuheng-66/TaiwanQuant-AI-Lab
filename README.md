# TaiwanQuant-AI-Lab

A local, reproducible research workbench for Taiwan listed equities. It generates
candidate momentum strategy modules, evaluates them with a fixed backtest harness,
and records every attempt. It never connects to a broker or calls a paid API.

## Quick start

Python 3.11+ is sufficient; the MVP has no runtime dependencies.

```bash
python3 -m taiwanquant validate path/to/bars.csv
python3 -m taiwanquant research path/to/bars.csv --train-end 2021-12-31 --valid-end 2023-12-31 --test-end 2024-12-31 --out runs/first
python3 -m taiwanquant test path/to/bars.csv --run runs/first
python3 -m taiwanquant snapshot twse --out data/raw
python3 -m taiwanquant snapshot tpex --out data/raw
python3 -m unittest discover -s tests -v
```

The CSV must contain `date,symbol,open,close,volume,available_at`. Prices must be
positive, split adjusted, in TWD, and from a source that permits your intended use.
`volume` is shares. `available_at` is an ISO 8601 timestamp with an offset and
represents when the complete row was actually available, not when it was dated.
The research command writes generated strategy code, a SHA-256 data fingerprint,
`experiments.jsonl`, and `summary.json`. The test command opens the holdout once
for the selected candidate and writes `holdout.json`.
Runs sharing a parent directory also share a local audit marker, so identical
data and test dates cannot be reopened from a sibling run directory. Keep all
run folders under one `runs/` directory to retain this guard.
By default, research uses three expanding validation folds of 60 market
sessions each, separated from training by five market sessions. The selected
candidate maximizes median fold validation return. For a very small fixture,
pass `--walk-forward-folds 1` to use a single train/validation split.
The input cap is 100 MB or 250,000 rows, the trial cap is 15, and the
experiment loop checks a monotonic wall-time deadline (120 seconds by default)
throughout evaluation. `--max-seconds` may be set from 1 to 3,600.
The snapshot command records an official daily response, retrieval timestamp,
source license page and SHA-256 hash under the Git-ignored `data/raw/` folder.
It is an observation, not a point-in-time historical dataset: the API does not
provide the original publication time of older records.

This is a research MVP, not a production trading system. It models next-session
open fills, board lots, fees, tax, slippage, and a volume cap; it does not model
limit-up/down queues, suspensions, corporate actions, dividends, settlement cash,
or survivorship-free universe construction. Those gaps block live trading and
credible claims of investment performance. See [RESEARCH.md](RESEARCH.md),
[ARCHITECTURE.md](ARCHITECTURE.md), and [TASKS.md](TASKS.md).

## Research rules

- The evaluation module is fixed during a research run. Generated candidates may
  change only their own strategy code.
- Train and validation windows are used for research. The holdout is opened once
  after selection; failed and rejected trials remain in the log.
- Data, generated code, settings, and outcomes are fingerprinted. Synthetic tests
  are explicitly identified and are never presented as market evidence.
- No real orders, credentials, private data, or paid APIs are used.

License: MIT; see [LICENSE](LICENSE).
