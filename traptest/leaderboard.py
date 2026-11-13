"""Per-provider leaderboard aggregation.

Ranking: pass rate first, then traps run (more evidence wins ties),
then lower total testnet cost. A provider with zero scored traps is
unranked — it is never shown as passing.

Unservable tier (Council finding F-rank): a provider that served
ZERO traps (every call failed before an answer — e.g. LiveCert 4433,
Sigil 9010, OnChain Intel 900 in the 6 Nov 2026 run) is NOT a 0%
provider. It goes in its own ``unservable`` tier via
:meth:`Leaderboard.mark_unservable` (or ``add(score, served=False)``)
and never appears in :meth:`Leaderboard.ranked`, above or below
served providers. A served provider that failed every trap it
answered IS ranked (at 0%) — failing answers are evidence; no
answers are not a pass rate.

``traptest/leaderboard.py`` is the single source of truth for this
aggregation. The leaderboard page (``docs/leaderboard/index.html``)
reads the ``unservable`` tier from the data file and filters those
providers out of the ranked table before ranking (verified 13 Nov
2026) — it no longer ranks unservable providers as 0% rows. (An
earlier NOTE here claimed the page still did; that was fixed, so
the NOTE was removed.)
"""
from dataclasses import dataclass, field


@dataclass
class ProviderStats:
    provider_id: str
    traps_run: int = 0
    passed: int = 0
    total_cost_usd: float = 0.0
    receipts: int = 0
    fields_correct: int = 0
    fields_scored: int = 0

    @property
    def pass_rate(self) -> float:
        return self.passed / self.traps_run if self.traps_run else 0.0

    @property
    def field_accuracy(self) -> float | None:
        """Field-weighted accuracy (co-primary metric, expansion set,
        9 Nov 2026): correct scored fields / all scored fields.
        None when no fields were scored."""
        if not self.fields_scored:
            return None
        return self.fields_correct / self.fields_scored

    @property
    def failed(self) -> int:
        return self.traps_run - self.passed


class Leaderboard:
    def __init__(self):
        self._stats: dict[str, ProviderStats] = {}
        self._unservable: set[str] = set()

    def add(self, score, served: bool = True) -> None:
        """Record one scored trap. ``served=False`` records the
        provider as unservable instead (no answer was served)."""
        if not served:
            self.mark_unservable(score.provider_id)
            return
        self._unservable.discard(score.provider_id)
        stats = self._stats.setdefault(score.provider_id,
                                       ProviderStats(score.provider_id))
        stats.traps_run += 1
        if score.passed:
            stats.passed += 1
        for f in (score.fields or ()):
            stats.fields_scored += 1
            if f.passed:
                stats.fields_correct += 1
        if score.cost_usd is not None:
            stats.total_cost_usd += float(score.cost_usd)
        if score.receipt_present:
            stats.receipts += 1

    def mark_unservable(self, provider_id: str) -> None:
        """Record a provider that served zero traps. It is kept out
        of ``ranked()`` permanently unless it later serves a trap
        (see ``add``)."""
        if provider_id not in self._stats:
            self._unservable.add(provider_id)

    # Backwards-friendly alias.
    add_unservable = mark_unservable

    def unservable_providers(self) -> list:
        """Provider ids that served zero traps, sorted. Never ranked."""
        return sorted(self._unservable)

    def ranked(self) -> list:
        ranked = [s for s in self._stats.values()
                  if s.traps_run > 0 and s.provider_id not in self._unservable]
        ranked.sort(key=lambda s: (-s.pass_rate, -s.traps_run,
                                   s.total_cost_usd, s.provider_id))
        return ranked
