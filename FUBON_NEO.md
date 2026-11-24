# Optional Fubon Neo market-data source (reviewed 2026-11-25)

Fubon Neo can supply local historical quote research data. This adapter is
optional; the public project remains runnable without a brokerage account.
It will never call an order endpoint. Raw account data, credentials, market
responses, and broker-derived datasets must stay outside the public Git repo.

## Official capabilities and limits

The [official historical-candles documentation](https://www.fbs.com.tw/TradeAPI/docs/market-data/http-api/historical/candles/)
says daily listed and OTC quotes go back to 2010, each request must span less
than one year, and daily history is updated by 16:30 after trading. It supports
`adjusted=true/false`; daily `volume` is in shares for common stocks, while
minute bars use lots. The [official rate-limit page](https://www.fbs.com.tw/TradeAPI/docs/market-data/rate-limit/)
sets historical requests at 60 per minute and describes HTTP 429 on excess.
The [corporate-actions endpoint](https://www.fbs.com.tw/TradeAPI/docs/market-data/http-api/corporate-actions/dividends/)
provides ex-dividend and ex-rights events. The [SDK page](https://www.fbs.com.tw/TradeAPI/docs/download/download-sdk/)
lists Python SDK 2.5.0 and API-key login support since 2.2.7; the
[login documentation](https://www.fbs.com.tw/TradeAPI/docs/trading/library/python/login/loginAPIKey/)
requires an identity, API key, certificate path and certificate password.

The [market-data usage terms](https://www.fbs.com.tw/TradeAPI/docs/market-data/intro/)
restrict retransmission, resale, sublicensing and some derivative uses of
market data. Public reproducibility should therefore use government open data
or synthetic fixtures; broker data should remain private unless separate
redistribution rights are confirmed. A brokerage announcement says the API
can be applied for free, but that does not by itself establish every user's
market-data charges. Confirm account-specific fees before making requests.

## Research boundary

- Use raw, unadjusted OHLC prices for simulated fills. An adjusted historical
  series may include later corporate actions and is not an executable price.
- Ex-dividend and capital changes must be modeled separately; unadjusted
  prices alone can create false momentum signals and false P&L.
- A historical API response fetched today does not prove when each old bar was
  first available. The documented 16:30 update is a general service rule,
  not a preserved per-bar publication timestamp. Any inferred availability
  should be labeled and sensitivity-tested with an additional one-day lag.
- Current security lists can omit delisted issues. Build an as-of universe and
  delisting treatment before claiming a survivor-free backtest.

`python3 -m taiwanquant fubon-inspect path/to/export.json --symbol 2330`
validates an exported daily-candle response locally and prints only schema
metadata. It never logs credentials or quote rows. Network retrieval and
normalization remain gated on the user's existing login setup and confirmed
account-specific fees.

The private adapter also exposes `fetch_daily_candles(authenticated_stock_client,
symbol, start, end, output_dir)`. It accepts an already authenticated SDK
stock client, requests unadjusted daily candles for fewer than 365 days,
validates the response, and saves quote bytes plus a provenance manifest in
`data/fubon/raw/`. It contains no login, order, or account-query code. It is
not invoked by the normal CLI or daily research automation.

## Existing Mac implementation inspected 2026-11-25

The user's `Desktop/fubon-market-monitor` project already authenticates with
Keychain and a local certificate. Its `MarketRuntime` uses
`sdk.apikey_login`, reads REST intraday quotes and WebSocket trades/books, and
stores records in local SQLite. The separate
`scripts/fetch_6770_research.py` uses the SDK's historical-candle endpoint to
cache 6770 one-minute bars in 14 local files spanning 2026-03-23 through
2026-09-22. A metadata-only inspection of the final file found 532 bars with
timezone-aware timestamps, `timeframe="1"`, `exchange="TWSE"`, and OHLC,
volume, and average fields; its SHA-256 is
`50c754b9d2b019e894a55c015988823ad6a9f65ef4f7f1fafc94780ded56bca0`.
No broker request or credential read was needed for this inspection.

Those minute files are private, cover one symbol, and do not declare an
adjustment policy or original publication times. They are useful as an
integration fixture, but cannot establish a survivor-free daily stock
backtest. Keep the existing Mac Keychain and certificate in place. A future
daily-bar retrieval can reuse the authenticated client in memory and pass it
to `fetch_daily_candles`; first confirm account-specific market-data fees and
that the saved response matches this project's daily schema. Do not commit
the Mac archive or its contents.
