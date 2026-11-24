# Research progress

2026-11-25: Literature and source review completed for RD-Agent,
Autoresearch, Qlib, TradingAgents and FinRobot at the pinned commits in
`RESEARCH.md`. Local MVP implemented. The next research gate is a licensed,
point-in-time Taiwan equities dataset. There are no market-performance
results yet. Every future run should append its path, data fingerprint,
window dates, selected trial, all failed trials and holdout status here.

2026-11-25: Verified the government open-data catalogue entries for TWSE
dataset 11549 and TPEx dataset 11370; both state free use under the Open
Government Data License v1 with attribution. Added an observed-time snapshot
command and manifest. No historical availability was inferred and no market
performance experiment was run. See `DATA_SOURCES.md`.

The first local captures were retrieved at 2026-11-25 00:40 Taiwan time:
TWSE had 1,394 rows dated 2026-11-23 (SHA-256
`728d702c0cce712701adae52105fd4d85b0e67f960e3faabcb3a1a7124f9272b`);
TPEx had 1,020 rows dated 2026-11-24 (SHA-256
`da063f8ce45670ca1cd25f2891ab73feee4b9c8b20bb43f4b32d3ce53deb3279`).
Raw files and manifests are in the Git-ignored `data/raw/` directory. They
were not used for performance analysis.

The evaluator now inserts late-arriving bars into history only once their
recorded availability time has passed, preserving market-date order.

Added expanding walk-forward folds with a configurable session embargo. The
default candidate selection now uses the median validation return across
three disjoint folds. No real market backtest was run.
Added input, row, trial and experiment wall-time limits; evaluation checks the
deadline during processing. The local synthetic and schema test suite now has
17 passing tests. No real market backtest was run.
The evaluator also rejects negative or non-finite transaction costs.

Added a shared local holdout audit marker for runs under one parent directory.
The same data hash and test dates cannot be reopened from a sibling run. The
guard is deliberately described as an audit aid, not tamper-proof security.

Corrected the TPEx catalogue reference from dataset 11370 to 11371 after
cross-checking the endpoint fields against the official closing-quotes entry.
The local manifest retains the previous reference and the correction note;
the captured bytes and SHA-256 are unchanged.

Reviewed Fubon Neo's official historical-candle and corporate-action APIs.
Its daily stock series reaches 2010, but current downloads do not preserve
the original publication timestamp or a survivor-free universe. Added an
offline inspector for private daily-candle exports. No login, broker request,
or order was made.
The offline suite has 20 passing tests after this adapter was added.
Added a read-only historical-candle fetch function requiring an already
authenticated Fubon stock client. It requests unadjusted daily bars for less
than 365 days and stores data only in Git-ignored local paths. No broker
request has been made. The suite now has 22 passing tests.
