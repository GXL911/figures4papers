import numpy as np
import pytest
from figures4papers import UncertaintySpec, summarize_seeds

def test_sd_and_sem_formulas():
    x=np.array([[1.,3.],[3.,7.],[5.,11.]])
    for kind in ("sd","sem"):
        s=summarize_seeds(x,UncertaintySpec(kind))
        sd=np.std(x,axis=0,ddof=1)
        delta=sd if kind=="sd" else sd/np.sqrt(3)
        np.testing.assert_allclose(s.upper,s.mean+delta)
        np.testing.assert_allclose(s.lower,s.mean-delta)
        assert s.n==3

def test_ci_and_bootstrap():
    x=np.array([[1,2],[2,3],[4,5],[5,6]])
    ci=summarize_seeds(x,UncertaintySpec("ci",0.95))
    assert np.all(ci.lower<=ci.mean) and np.all(ci.mean<=ci.upper)
    spec=UncertaintySpec("bootstrap_ci",0.95,n_resamples=200,seed=19)
    a=summarize_seeds(x,spec)
    b=summarize_seeds(x,spec)
    np.testing.assert_array_equal(a.lower,b.lower)
    np.testing.assert_array_equal(a.upper,b.upper)

def test_no_imagined_uncertainty():
    s=summarize_seeds([1,2,3],UncertaintySpec("none"))
    assert s.lower is None and s.upper is None
    with pytest.raises(ValueError): summarize_seeds([1],UncertaintySpec("sem"))

def test_reject_invalid_ci_and_dependent_data():
    for args in [dict(kind="ci",confidence_level=1.0),
                 dict(kind="ci"),
                 dict(kind="bootstrap_ci",confidence_level=0.95,n_resamples=3),
                 dict(kind="sem",independent_replicates=False)]:
        with pytest.raises(ValueError): UncertaintySpec(**args)
