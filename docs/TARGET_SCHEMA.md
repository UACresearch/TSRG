# R20 camera target schema

The older textual CE supervision used `original_horizontal_fov` (radians), while official center-square benchmarking expects vertical FoV for the square crop. The conversion is:

```python
square_vfov_deg = degrees(2 * atan(min(W,H) / W * tan(original_hfov_rad / 2)))
```

Roll and pitch in the historical text target must also be converted from radians to degrees for comparison with the new degree-valued targets. The historical audit found exact matching for parsed labels once these conversions were applied; do not transfer the old text labels unchanged as square-vFoV labels. Note that this formula assumes a pinhole camera and a centered square crop; it is not a universal correction for arbitrary warping, rectification or off-center cropping.

Target references in R20 are GeoCalib pseudo-labels filtered by declared quality criteria. The R20 evaluation should be described as agreement with a specified pseudo-reference, not external ground-truth validation.
