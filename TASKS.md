# Research tasks

## Completed 2026-11-25

- [x] Review the five upstream READMEs, core implementation boundaries,
  dependency manifests, licenses, and linked papers.
- [x] Define Taiwan market data and backtest assumptions.
- [x] Build the local CPU research loop, fixed evaluator, experiment log,
  candidate hashes, and one-shot holdout command.
- [x] Add targeted tests for leakage, next-open execution, costs, and records.
- [x] Verify official free daily TWSE/TPEx dataset licenses and add a
  provenance-preserving snapshot command with schema tests.
- [x] Preserve market-date order when delayed rows become available to a signal.
- [x] Add expanding, disjoint walk-forward validation folds with a session embargo.
- [x] Bound input size, row count, trial count and experiment wall time.
- [x] Prevent reopening the same data fingerprint and holdout dates across
  sibling research runs with a persistent local audit marker.

## Next

- [ ] Obtain a survivorship-aware historical TWSE/TPEX dataset and verify its
  specific license, publication lag, adjustment method and delisting coverage.
  Keep raw rows outside Git. The licensed daily feeds alone are insufficient.
- [ ] Add split/dividend/delisting adjustments and orderability checks for
  limit-up/down and suspensions.
- [ ] Add benchmark, risk-adjusted predeclared metric and uncertainty estimates;
  disclose any final-period selection across different datasets or run groups.
- [ ] Implement a constrained optional local-model proposer and isolated
  execution process with CPU, memory and wall-time limits.
- [ ] Publish a reproducible research note with every run and negative result.

## Work session state

Date: 2026-11-25. Phase: MVP complete; genuine market-data evaluation pending.
No real market backtest has been run and no return claim has been made.
Resume by checking `RESEARCH.md`, this checklist, and the latest run directory.
