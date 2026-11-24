# Research tasks

## Completed 2026-11-25

- [x] Review the five upstream READMEs, core implementation boundaries,
  dependency manifests, licenses, and linked papers.
- [x] Define Taiwan market data and backtest assumptions.
- [x] Build the local CPU research loop, fixed evaluator, experiment log,
  candidate hashes, and one-shot holdout command.
- [x] Add targeted tests for leakage, next-open execution, costs, and records.

## Next

- [ ] Obtain and license-check a survivorship-aware TWSE/TPEX dataset. Record
  source URL, retrieval time, publication lag, adjustment and redistribution
  rights. Keep raw rows outside Git.
- [ ] Add split/dividend/delisting adjustments and orderability checks for
  limit-up/down and suspensions.
- [ ] Add purged walk-forward folds, predeclared metric, benchmark and
  uncertainty estimates; prohibit repeated final-period selection.
- [ ] Implement a constrained optional local-model proposer and isolated
  execution process with CPU, memory and wall-time limits.
- [ ] Publish a reproducible research note with every run and negative result.

## Work session state

Date: 2026-11-25. Phase: MVP complete; genuine market-data evaluation pending.
No real market backtest has been run and no return claim has been made.
Resume by checking `RESEARCH.md`, this checklist, and the latest run directory.
