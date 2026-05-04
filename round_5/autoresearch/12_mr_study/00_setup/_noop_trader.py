"""No-op trader — baseline for timing the backtester."""
from datamodel import OrderDepth, TradingState  # noqa: F401


class Trader:
    def run(self, state):
        return {}, 0, ""
