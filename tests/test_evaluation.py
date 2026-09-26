import pytest
from tsrg.evaluation import PitchRow,paired_pitch_mae,location_cluster_bootstrap_delta


def test_paired_pitch_mae():
    rows=[PitchRow('a',0,3,2), PitchRow('a',1,4,2), PitchRow('b',0,2,1)]
    r=paired_pitch_mae(rows)
    assert r.n==3 and r.locations==2
    assert r.m0_mae_deg==pytest.approx(8/3)
    assert r.m2_mae_deg==pytest.approx(4/3)
    assert r.delta_m2_minus_m0_deg==pytest.approx(-4/3)


def test_bootstrap_reproducible_and_negative():
    rows=[PitchRow('a',0,3,2), PitchRow('a',1,4,2), PitchRow('b',0,2,1)]
    a=location_cluster_bootstrap_delta(rows,n_boot=300,seed=7)
    assert a == location_cluster_bootstrap_delta(rows,n_boot=300,seed=7)
    assert a['ci95'][1] < 0
    assert a['descriptive_fraction_negative'] == 1


def test_reject_empty():
    with pytest.raises(ValueError): paired_pitch_mae([])
