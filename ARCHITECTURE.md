# Architecture and validation contract

```text
Licensed, point-in-time CSV
  -> schema and provenance validator -> immutable dated bars
  -> rule-based hypothesis proposer -> generated candidate Python modules
  -> fixed next-open portfolio evaluator -> train/validation experiment log
  -> one-shot holdout audit -> progress and daily report
```

An additional capture path stores official TWSE and TPEx daily JSON responses
with observed retrieval timestamps and SHA-256 manifests under `data/raw/`.
Those captures are evidence for a future point-in-time archive; they are not
silently converted into historical publication times. See `DATA_SOURCES.md`.

`taiwanquant/core.py` is the evaluation boundary. The proposer writes code
artifacts containing literal strategy parameters; the runner parses those
parameters without executing arbitrary code. Later LLM adapters may propose
changes to a constrained strategy interface, but must not edit the evaluator,
data, cost model or split definitions. Each trial logs a candidate hash and
train/validation metrics or a failure. The raw data file is hashed and excluded
from Git.

The data contract requires a timezone-aware publication timestamp for each
daily bar. A signal at 18:00 Asia/Taipei sees only published rows and orders
are simulated at the next available market open. A position is rounded to
1,000 shares and an order is capped at 1% of that day's reported share volume.
Cash, shares, fees, sell tax and slippage are tracked. The simulation never
sends orders to a broker.
Late-arriving rows enter the feature history only after their recorded
availability time; history remains ordered by market date.

`research` consumes a chronological train window and a validation window. It
never computes test-period metrics. `test` checks data and candidate hashes,
marks the holdout as opened before evaluation, and writes the result or failure.
Once opened, that run cannot be retested through the CLI. This is an audit aid,
not tamper-proof security. A fresh run still allows repeated testing; research
reports must disclose all such runs.

The current scorer selects by validation total return. It is intentionally
simple and should be replaced by a predeclared, risk-adjusted objective and
walk-forward evaluation before publication. The current backtest ignores
corporate actions, dividends, limit queues and settlement constraints. It
must not be interpreted as executable strategy P&L.
