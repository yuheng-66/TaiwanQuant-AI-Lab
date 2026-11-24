# Research review (2026-11-25)

Five upstream repositories were reviewed at the following commits. This is a
design review, not a reproduction of their reported investment results. GitHub
README, selected core source files, dependency manifests, licenses, and linked
papers were inspected. Upstream code was not copied into this project.

| Project | Commit | Architecture and useful idea | Strength | Limitation for this project | License / key dependencies / compute |
|---|---|---|---|---|---|
| [RD-Agent](https://github.com/microsoft/RD-Agent) | `484776c` | Research, development and feedback loop; `rdagent/core/evolving_framework.py`, `experiment.py`; [technical report](https://arxiv.org/abs/2505.14738), [quant paper](https://arxiv.org/abs/2505.15155) | Explicit experiment abstraction and factor/model iteration | Broad framework, Docker and model API configuration raise setup and cost | MIT; Python, Docker for most scenarios, LLM endpoint; CPU plus optional remote model compute |
| [Autoresearch](https://github.com/karpathy/autoresearch) | `228791f` | Immutable `prepare.py`, mutable `train.py`, agent instructions in `program.md`, fixed five-minute budget | Very clear experiment boundary, comparable local runs, keep/discard log | Objective is language-model loss, not point-in-time financial return; single GPU required | README says MIT; no LICENSE file in inspected tree, so confirm licensing before reusing code; PyTorch CUDA, kernels, NumPy, PyArrow; tested H100 NVIDIA GPU |
| [Qlib](https://github.com/microsoft/qlib) | `5435523` | `qlib/data/dataset/handler.py`, `backtest/backtest.py`, `workflow/recorder.py`; [paper](https://arxiv.org/abs/2009.11189) | Mature data/model/backtest/record separation | Large dependency and provider stack; Taiwan coverage and point-in-time data still need local work | MIT; Python, NumPy/Cython and optional ML stacks; CPU feasible for simple models, heavier models may need GPU |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | `81501e0` | Role agents in `src/agents`, risk and portfolio computation in `src/compute`, stateful engine in `src/engine`; [paper](https://arxiv.org/abs/2412.20138) | Useful debate and risk-review pattern | LLM and data-provider API dependence; trading narratives can obscure measurable edge; current TypeScript app is much larger than an MVP | Apache-2.0; Node >=22, AI SDK/provider packages, data API key; model calls dominate cost |
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot) | `63e1884` | V0 AutoGen research agents and V1 deterministic valuation operators with LLM explanation; [paper](https://arxiv.org/abs/2405.14767) | Separates numeric computation from language synthesis, with traceable provenance | Multiple generations and desktop/web stacks are costly to maintain; API keys needed for full demos | Apache-2.0; Python, AutoGen/OpenAI Agents SDK, optional React/Tauri; CPU plus remote LLM/API service |

## Design decisions

1. **Adopt concepts, not frameworks.** Keep a small local Python package, a
   fixed evaluator, and generated candidate modules. No upstream code is
   embedded. The agent boundary is a future adapter; today's proposer is a
   deterministic template engine so experiments run without a model subscription.
2. **Use two clocks.** A market row has a trading date and an `available_at`
   timestamp. A decision at 18:00 Taiwan time may use only rows available by
   then. Signals execute at the next session's open. This is the project's
   first technical contribution: a simple, inspectable provenance gate that
   makes look-ahead assumptions visible in every imported dataset.
3. **Separate selection and audit.** Candidate search uses train and validation
   windows; one selected candidate can be evaluated on a sealed test period
   once per run. Report all attempts, including failures. Multiple validation
   comparisons still create selection bias, so use a small trial budget and
   repeat on independent walk-forward folds in the next phase.
4. **Taiwan costs and trading mechanics.** Listed-stock sales use a 0.3% tax
   assumption, consistent with the [TWSE investment guide](https://accessibility.twse.com.tw/zh/about/company/guide.html).
   The assumed broker commission is 0.1425% per side and slippage 0.1% per side;
   both are configurable research assumptions, not quotes for a particular
   broker. TWSE describes 1,000-share board lots and a 9:00–13:30 regular
   session in its [trading mechanism guide](https://www.twse.com.tw/en/products/system/trading.html).
5. **Data rights.** Public availability does not imply redistribution rights.
   The [TWSE OpenAPI](https://openapi.twse.com.tw/) lists daily market endpoints,
   while the [TWSE website terms](https://wwwc.twse.com.tw/en/terms/use.html)
   restrict reuse except material authorized as government open data. Keep raw
   datasets out of Git; verify a dataset's specific license before publishing.

## Risks to resolve before any credible market claim

- Point-in-time constituent membership and delisted symbols; no survivor-only
  universe. Include publication timestamps for fundamentals and revisions.
- Corporate actions: consistent split-adjusted open/close, dividends and
  delisting cash flows. Verify volume units and adjustment methodology.
- Limit-up/down, suspended issues, liquidity, tick sizes, odd lots, fees with
  actual broker minima, and settlement cash. Current fills are idealized.
- Purged walk-forward folds with embargo based on target horizon, a frozen
  benchmark, turnover and exposure limits, bootstrap uncertainty, and a
  second untouched market regime. Never tune on the final holdout.
- Independent reproduction using permitted TWSE/TPEX data. The five papers'
  reported returns do not transfer to Taiwan equities.

## Source-specific observations

- RD-Agent-Quant proposes factor/model co-optimization and feedback, but its
  empirical results are paper claims, not evidence for this MVP.
- Autoresearch's fixed five-minute GPU budget is an analogy: this project caps
  trials and wall time on CPU, and holds the evaluation code fixed.
- Qlib could become an optional benchmark integration after the local data and
  point-in-time contracts are validated.
- TradingAgents' bull/bear review is reserved for hypothesis critique, never
  for producing numeric performance metrics.
- FinRobot's deterministic calculation principle is applied directly: the
  evaluator computes metrics; any future LLM only proposes or explains.
