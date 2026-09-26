import math
import pytest
from tsrg.camera import original_hfov_to_square_vfov_deg, radians_to_degrees


def test_original_square_image_preserves_fov():
    assert original_hfov_to_square_vfov_deg(math.radians(60), 100, 100) == pytest.approx(60)


def test_portrait_full_width_also_preserves_fov():
    assert original_hfov_to_square_vfov_deg(math.radians(60), 100, 200) == pytest.approx(60)


def test_landscape_square_crop_reduces_fov():
    expected=math.degrees(2*math.atan((100/200)*math.tan(math.radians(60)/2)))
    assert original_hfov_to_square_vfov_deg(math.radians(60), 200, 100) == pytest.approx(expected)
    assert expected < 60


def test_radians_to_degrees():
    assert radians_to_degrees(math.pi/2) == pytest.approx(90)

@pytest.mark.parametrize('fov,w,h',[(0,100,100),(math.pi,100,100),(.5,0,100),(.5,100,-1),(float('nan'),100,100)])
def test_reject_bad_parameters(fov,w,h):
    with pytest.raises(ValueError): original_hfov_to_square_vfov_deg(fov,w,h)
