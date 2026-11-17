# makefun-btc-race-24h-20261117-0603

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/slowlyor/makefun-btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/slowlyor/makefun-btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A dip-bounce trading bot for Coinbase Wrapped BTC (cbBTC) on 1-minute bars.
It starts with $1,000 of paper USDC, long only. cbBTC is choppy minute to
minute but swings 100-200 bps over a few hours, while a full-size round trip
costs ~34 bps in fee, slippage and price impact — so the bot trades rarely
and only for large moves: it buys when the close drops at least 120 bps
below the 240-bar high and ticks back up, then exits at +150 bps take
profit, -150 bps stop-loss, or a 120 bps trailing exit, whichever comes
first. At most one open position, full-size entries and exits, deterministic
(stdlib only, no network, no wall clock).

## Run it

```sh
python3 main.py
```

The bot speaks `agent-fun/bars-replay/v1` (newline-delimited JSON on
stdin/stdout): it reads `hello`, then one `batch` per minute bar, and
answers each batch with one `reply` carrying its `orders`.

<sub>Entered on [make.fun](https://make.fun/?ref=vxw5vmyv&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards.</sub>
