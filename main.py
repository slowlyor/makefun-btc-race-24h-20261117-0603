"""Dip-bounce BTC trading bot for make.fun's btc-race-24h-20261117-0603.

Speaks agent-fun/bars-replay/v1 (hello, then one batch per 1-minute bar,
one reply with orders per batch) through the vendored makefun_bars shim.

Strategy (designed from the dev window's 1,440 cbBTC bars):
  * cbBTC on this pool is choppy at the 1-minute scale (stdev ~6 bps/min)
    but swings 100-200 bps over a few hours, while a full-size round trip
    costs ~34 bps in fee + slippage + price impact. So the bot trades
    rarely and only for large moves: it buys a deep dip and sells the
    bounce, never chasing every wiggle.
  * Entry (flat only): the latest close is at least 120 bps below the
    highest close of the last 240 bars AND the bar ticked up from the
    previous close (a first sign the dip is turning, not still falling).
    Buys with 100% of cash.
  * Exit (long only): take profit at +150 bps over the fill price,
    stop-loss at -150 bps, or a trailing exit 120 bps below the highest
    close since entry, whichever comes first.
  * Risk controls: at most one open position, long only, full-position
    exits, max_slippage_bps 100 on every order so a wild next-bar open
    rejects the order instead of filling at a bad price. No trading
    during warm-up batches.

Deterministic: no randomness, no wall clock, no network, no files
outside the repository. All decisions come from the bars in the batch
stream and the account the harness reports.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Strategy parameters (basis points; 100 bps = 1%).
LOOKBACK_BARS = 240      # window for the dip reference high
DIP_BPS = 120            # buy when close is this far below the lookback high
TAKE_PROFIT_BPS = 150    # sell when up this far from the fill price
STOP_LOSS_BPS = 150      # sell when down this far from the fill price
TRAIL_BPS = 120          # sell when this far below the post-entry peak
MAX_SLIPPAGE_BPS = 100   # reject the fill if the next open moves this far
LATE_ENTRY_CUTOFF = 1380  # no new buys in the final hour: a position opened
                          # there cannot develop before the forced flatten
                          # at the last close, it would only pay the
                          # ~34 bps round-trip cost (both windows are
                          # 1,440 bars)


class DipBounceBot:
    """State for one run: close history plus the live position's anchor."""

    def __init__(self):
        self.closes = []          # closes, oldest first, in price units
        self.entry_px = None      # fill price of the open position (or None)
        self.peak_px = None       # highest close since entry (or None)

    def on_batch(self, state, batch):
        # Fold in this batch's fills first: they set (or clear) the anchor.
        for fill in batch.get("fills", []):
            if fill.get("status") != "filled" or fill.get("symbol") != SYMBOL:
                continue
            if fill["side"] == "buy":
                self.entry_px = int(fill["price"])
                self.peak_px = self.entry_px
            else:
                self.entry_px = None
                self.peak_px = None

        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)

        if state.warming_up:
            return []

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding else 0

        if qty > 0:
            return self._maybe_exit(state, close)
        return self._maybe_enter(state, close)

    def _maybe_enter(self, state, close):
        if len(self.closes) <= LOOKBACK_BARS:
            return []
        if state.seq >= LATE_ENTRY_CUTOFF:
            return []
        if state.cash <= int(state.hello["fees"]["min_notional_quote_units"]):
            return []
        window = self.closes[-LOOKBACK_BARS - 1:]
        high = max(window)
        dip_bps = (high - close) * 10_000 // high if high > 0 else 0
        ticked_up = close > self.closes[-2]
        if dip_bps >= DIP_BPS and ticked_up:
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    def _maybe_exit(self, state, close):
        if self.entry_px is None:
            # Position exists but we never saw its fill (should not happen);
            # hold it: exiting blind would be guessing.
            return []
        if close > self.peak_px:
            self.peak_px = close
        gain_bps = (close - self.entry_px) * 10_000 // self.entry_px
        trail_bps = (self.peak_px - close) * 10_000 // self.peak_px
        if (gain_bps >= TAKE_PROFIT_BPS
                or gain_bps <= -STOP_LOSS_BPS
                or trail_bps >= TRAIL_BPS):
            holding = state.positions[SYMBOL]
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": holding.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []


def main():
    bot = DipBounceBot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
