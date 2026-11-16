import numpy as np
import matplotlib.pyplot as plt
import pytest
from figures4papers import (ValidationError, validate_numeric_array,
    validate_grouped_inputs, validate_intervals, validate_reliability,
    validate_figure, validate_bar_artists, validate_line_artist)

def test_finite_and_dimensions():
    assert validate_numeric_array([1,2],ndim=1).shape==(2,)
    for x in ([1,np.nan],[1,np.inf],["a"],[]):
        with pytest.raises(ValidationError): validate_numeric_array(x)
    assert np.isnan(validate_numeric_array([np.nan],allow_nan=True)).any()
    with pytest.raises(ValidationError):
        validate_numeric_array([np.inf],allow_nan=True)

def test_shapes_and_uncertainty_metadata():
    assert validate_grouped_inputs(["A","B"],[[1,2]],["M"]).shape==(1,2)
    bad=[
        (["A"],[[1,2]],["M"],None,None),
        (["A","A"],[[1,2]],["M"],None,None),
        (["A"],[[1],[2]],["M","M"],None,None),
        (["A"],[[1]],["M"],[[0.1]],None),
        (["A"],[[1]],["M"],[[-0.1]],"sd"),
    ]
    for cats,series,labels,errors,kind in bad:
        with pytest.raises(ValidationError):
            validate_grouped_inputs(cats,series,labels,yerr=errors,uncertainty_kind=kind)
    validate_grouped_inputs(["A"],[[1]],["M"],yerr=[[0.1]],uncertainty_kind="sem")

def test_bad_intervals_and_coverage():
    validate_intervals([0.5],[0.4],[0.6])
    with pytest.raises(ValidationError): validate_intervals([0.5],[0.6],[0.7])
    with pytest.raises(ValidationError): validate_intervals([0.5,0.6],[0.3],[0.7])
    validate_reliability([0.5,0.9],[0.4,0.8])
    for n,e in [([0.9,0.5],[0.4,0.8]),([0.5],[1.3]),([0.5,0.9],[0.6,0.4])]:
        with pytest.raises(ValidationError): validate_reliability(n,e)

def test_artist_matches_source():
    fig,ax=plt.subplots()
    bars=ax.bar([0,1],[0.2,0.7])
    validate_bar_artists(bars,[0.2,0.7])
    with pytest.raises(ValidationError): validate_bar_artists(bars,[0.2,0.6])
    line,=ax.plot([0,1],[1,2])
    validate_line_artist(line,[0,1],[1,2])
    with pytest.raises(ValidationError): validate_line_artist(line,[0,1],[1,3])
    plt.close(fig)

def test_nonzero_bar_baseline_warns():
    fig,ax=plt.subplots()
    ax.bar([0],[0.9])
    ax.set_ylim(0.8,1)
    codes={v.code for v in validate_figure(fig)}
    assert "truncated_bar_axis" in codes and "missing_x_label" in codes
    plt.close(fig)

def test_empty_figure():
    fig=plt.figure()
    with pytest.raises(ValidationError): validate_figure(fig)
    plt.close(fig)

def test_color_semantics_across_panels():
    from figures4papers import validate_color_semantics
    fig,axes=plt.subplots(1,2)
    axes[0].plot([0,1],[1,2],label="Proposed",color="#0F4D92")
    axes[1].plot([0,1],[1,2],label="Proposed",color="#B64342")
    issues=validate_color_semantics(fig)
    assert "inconsistent_series_color" in [item.code for item in issues]
    plt.close(fig)
