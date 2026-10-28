"""Per-provider leaderboard aggregation.

Ranking: pass rate first, then traps run (more evidence wins ties),
then lower total testnet cost. A provider with zero scored traps is
unranked — it is never shown as passing.
"""
from dataclasses import dataclass, field


@dataclass
class ProviderStats:
    provider_id: str
    traps_run: int = 0
    passed: int = 0
    total_cost_usd: float = 0.0
    receipts: int = 0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.traps_run if self.traps_run else 0.0

    @property
    def failed(self) -> int:
        return self.traps_run - self.passed


class Leaderboard:
    def __init__(self):
        self._stats: dict[str, ProviderStats] = {}

    def add(self, score) -> None:
        stats = self._stats.setdefault(score.provider_id,
                                      ProviderStats(score.provider_id))
        stats.traps_run += 1
        if score.passed:
            stats.passed += 1
        if score.cost_usd is not None:
            stats.total_cost_usd += float(score.cost_usd)
        if score.receipt_present:
            stats.receipts += 1

    def ranked(self) -> list:
        ranked = [s for s in self._stats.values() if s.traps_run > 0]
        ranked.sort(key=lambda s: (-s.pass_rate, -s.traps_run,
                                   s.total_cost_usd, s.provider_id))
        return ranked
