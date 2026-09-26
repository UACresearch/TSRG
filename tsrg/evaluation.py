"""Paired pitch MAE and location-cluster bootstrap (descriptive)."""
from collections import defaultdict
from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class PitchRow:
    location_id: str
    reference_deg: float
    m0_deg: float
    m2_deg: float


@dataclass(frozen=True)
class PairedMAE:
    n: int
    locations: int
    m0_mae_deg: float
    m2_mae_deg: float
    delta_m2_minus_m0_deg: float
    relative_change_pct: float


def _validate(rows):
    rows = tuple(rows)
    if not rows:
        raise ValueError("need at least one paired row")
    for r in rows:
        if not r.location_id or not all(map(math.isfinite, (r.reference_deg, r.m0_deg, r.m2_deg))):
            raise ValueError("each row requires a location and finite paired values")
    return rows


def paired_pitch_mae(rows) -> PairedMAE:
    rows = _validate(rows)
    m0 = sum(abs(r.m0_deg-r.reference_deg) for r in rows)/len(rows)
    m2 = sum(abs(r.m2_deg-r.reference_deg) for r in rows)/len(rows)
    return PairedMAE(len(rows), len({r.location_id for r in rows}), m0, m2, m2-m0, 100*(m2-m0)/m0 if m0 else float('nan'))


def location_cluster_bootstrap_delta(rows, *, n_boot: int=10000, seed: int=20260926) -> dict:
    """Resample location IDs, keep every image within each sampled location.

    Delta is M2 MAE minus M0 MAE; negative values indicate smaller M2 MAE.
    Confidence intervals are descriptive, not a licence for post-hoc test tuning.
    """
    rows = _validate(rows)
    if not isinstance(n_boot,int) or n_boot < 1:
        raise ValueError("n_boot must be a positive integer")
    groups = defaultdict(list)
    for r in rows:
        groups[r.location_id].append(r)
    groups = list(groups.values())
    n_groups = len(groups)
    sums = [(len(g), sum(abs(r.m0_deg-r.reference_deg) for r in g), sum(abs(r.m2_deg-r.reference_deg) for r in g)) for g in groups]
    rng = random.Random(seed)
    samples = []
    for _ in range(n_boot):
        draws = [sums[rng.randrange(n_groups)] for __ in range(n_groups)]
        n = sum(s[0] for s in draws)
        samples.append((sum(s[2] for s in draws) - sum(s[1] for s in draws)) / n)
    samples.sort()
    def percentile(q):
        idx = (len(samples)-1)*q
        lo,hi=math.floor(idx),math.ceil(idx)
        return samples[lo]*(hi-idx)+samples[hi]*(idx-lo) if hi>lo else samples[lo]
    return dict(n_locations=n_groups, n_boot=n_boot, seed=seed, ci95=[percentile(.025),percentile(.975)], descriptive_fraction_negative=sum(x<0 for x in samples)/n_boot)
