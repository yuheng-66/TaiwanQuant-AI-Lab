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
The experiment runner now logs and rejects any candidate with zero trades in
a training or validation fold.
The suite now has 23 passing tests.

Inspected the user's `Desktop/fubon-market-monitor` on their Mac. It already
has a Keychain-backed SDK login path, an intraday SQLite recorder, and a
read-only historical minute-candle script. Fourteen private 6770 archive
files span 2026-03-23 to 2026-09-22. The last file contains 532 minute bars
for 2026-09-21 to 2026-09-22 and has SHA-256
`50c754b9d2b019e894a55c015988823ad6a9f65ef4f7f1fafc94780ded56bca0`.
This was metadata-only inspection; no credentials, live broker requests,
orders, or market-performance experiments were involved. See `FUBON_NEO.md`.

The Fubon daily-candle validator now requires finite high and low values and
rejects OHLC ranges that exclude the opening or closing price. One targeted
synthetic test covers an inconsistent high. The offline suite has 24 passing
tests. No broker request or market-performance experiment was run. A new live
request remains blocked because the user's Mac connection does not grant
terminal execution; do not bypass that access boundary.

The backtest previously sized next-open orders with the execution day's
completed-session volume, a look-ahead input. It now caps buy and sell size
using the latest daily volume published by the preceding decision time.
A synthetic test checks that a high-volume execution day cannot enlarge an
order when the prior known volume permits no board lot. The offline suite has
25 passing tests. No market-data experiment or performance claim was made.
The execution-day zero-volume no-fill rule remains a retrospective proxy
until opening auction and suspension data are available.

Corrected maximum drawdown to start from initial cash rather than the first
observed session's closing equity. Before this change, a loss from costs or
price movement in the first evaluated session could be omitted. A synthetic
case with an opening purchase and commission now checks for negative
drawdown. The offline suite has 26 passing tests. No broker request,
market-data experiment or performance claim was made.

2026-11-26: Tested the daily CSV publication-time floor using Python 3.11.2.
The synthetic fixture in `test_daily_bar_requires_availability_at_or_after_regular_close`
uses a 2024-01-02 bar for 2330 with open and close of 10 and volume of
1,000 shares. The test varies availability across 05:29:59 UTC and
05:30:00 UTC on January 2, and 01:00 Taiwan time on January 3.
The targeted test initially failed on the pre-close case against base
commit `5eddf52149a07a7e409fb380acb148e88526fda3` with the new fixture.
After the validator change, all 27 tests passed via
`python3 -m unittest discover -s tests`. Git blob IDs for the tested
validator and fixture files are `f82457ce9ce016e1fce91cb612a2e1a99807eb6b`
and `b5d5f47fd153e8cbce5c8c7fe18ef795bce8311c`, respectively.
No historical market dataset or broker feed was used. Verifying the
actual publication lag, licensing and delisting coverage remains open.
