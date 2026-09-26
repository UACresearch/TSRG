import pytest
from tsrg.routing import CameraPrediction, m2_par_prediction

@pytest.mark.parametrize('category', ['event','heritage'])
def test_specialist_only_replaces_pitch(category):
    m0 = CameraPrediction(roll_deg=1.2,pitch_deg=-2.0,square_vfov_deg=45.5)
    result=m2_par_prediction(category,m0,3.0)
    assert result == CameraPrediction(1.2,3.0,45.5)

@pytest.mark.parametrize('category', ['natural','purpose_built'])
def test_baseline_categories_unchanged(category):
    m0 = CameraPrediction(1.2,-2.0,45.5)
    assert m2_par_prediction(category,m0)==m0


def test_specialist_required():
    with pytest.raises(ValueError): m2_par_prediction('heritage',CameraPrediction(0,0,50))


def test_unknown_category_fails():
    with pytest.raises(ValueError): m2_par_prediction('other',CameraPrediction(0,0,50))
