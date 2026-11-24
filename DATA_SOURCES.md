# Taiwan quote data provenance (reviewed 2026-11-25)

The government open data catalogue lists [TWSE listed daily security
transactions](https://data.gov.tw/dataset/11549) and [TPEx OTC daily
quotes](https://data.gov.tw/dataset/11370) as free datasets under the
[Open Government Data License v1](https://data.gov.tw/license). The license
permits reuse with explicit attribution. The source pages name the Securities
and Futures Bureau as the provider and link the exchanges' OpenAPI documents.
The [TPEx website terms](https://www.tpex.org.tw/zh-tw/gtsm_disclaimer.html?l=zh-tw)
also distinguish government-open-data material from other website content.
This project treats only the identified datasets as licensed; it does not
assume all exchange data can be redistributed.

| Market | Endpoint captured | Catalogue page | Fields used for sanity checks |
|---|---|---|---|
| TWSE listed | `https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL` | [11549](https://data.gov.tw/dataset/11549) | `Date`, `Code`, `OpeningPrice`, `ClosingPrice`, `TradeVolume` |
| TPEx OTC | `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes` | [11370](https://data.gov.tw/dataset/11370) | `Date`, `SecuritiesCompanyCode`, `Open`, `Close`, `TradingShares` |

The endpoints contain ETFs and other instruments as well as stocks. Asset
classification is required before a listed-stock tax model or equity-only
universe can be applied. The response may contain a market date older than
the retrieval date; `snapshot` records both. It never substitutes retrieval
time for the unknown original publication time of historical records.

On 2026-11-25 around 00:39 Taiwan time, a read-only inspection found 1,394
TWSE rows with a sample market date of 2026-11-23, and 1,020 TPEx rows with a
sample market date of 2026-11-24. These counts and dates are observations of
the endpoints at that time, not backtest inputs. The raw responses were not
published or retained by that inspection.

Run `python3 -m taiwanquant snapshot twse` or `... snapshot tpex` to preserve
a raw response and manifest under Git-ignored `data/raw/`. The manifest holds
the retrieval time, observed market dates, byte hash, row count, source URL,
and license page. Check the manifest and source catalogue license before any
reuse. Do not publish captured snapshots until attribution and instrument
coverage have been reviewed.

**Remaining data gate:** a historical, survivor-free universe, corporate
action adjustments, publication timestamps and delisting outcomes are still
needed before credible strategy backtests. Current daily endpoints alone do
not meet that gate.
