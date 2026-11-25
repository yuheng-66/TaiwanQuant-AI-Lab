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
1,000 shares and an order is capped at 1% of the latest previously published
daily share volume. The execution day's full-session volume is not available
at the open and is not used to size orders. A zero-volume execution-day row is
still used as a retrospective no-fill proxy; a proper opening auction and
suspension feed remains necessary.
Cash, shares, fees, sell tax and slippage are tracked. The simulation never
sends orders to a broker.
Late-arriving rows enter the feature history only after their recorded
availability time; history remains ordered by market date.

`research` consumes chronological expanding train windows and disjoint
validation windows, with a five-session default embargo. The median fold
validation return chooses a candidate; the fold boundaries and scores are
recorded. It never computes test-period metrics. `test` checks data and candidate hashes,
marks the holdout as opened before evaluation, and writes the result or failure.
Once opened, that run cannot be retested through the CLI. This is an audit aid,
not tamper-proof security. A persistent marker in the parent run directory
also blocks the same data fingerprint and test dates across sibling runs.
Copying the data or moving runs to a new parent can bypass it; research reports
must disclose all such runs.

The current scorer selects by median fold validation total return. It is
intentionally simple and should be replaced by a predeclared, risk-adjusted
objective with uncertainty estimates before publication. The current backtest ignores
corporate actions, dividends, limit queues and settlement constraints. It
must not be interpreted as executable strategy P&L.
Maximum drawdown includes the initial cash balance as the pre-trading equity
peak, so a loss incurred in the first evaluated session is counted.

The current input guard rejects files over 100 MB or 250,000 rows. Candidate
search is limited to 15 trials, with a monotonic deadline checked during each
evaluation. These are CPU and input bounds; process-level memory isolation is
still a planned improvement before accepting generated arbitrary strategy code.
