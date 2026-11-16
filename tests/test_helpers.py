import numpy as np
import matplotlib.pyplot as plt
import pytest
from figures4papers import (
    FigureStyle, apply_publication_style, create_subplots,
    make_grouped_bar, make_learning_curves, make_heatmap,
    make_trend, make_reliability_diagram, make_scatter, ValidationError)

def test_style_and_subplots():
    apply_publication_style(FigureStyle(font_size=12))
    fig,axes=create_subplots(2,2)
    assert len(axes)==4
    plt.close(fig)
    with pytest.raises(ValueError): FigureStyle(font_size=0)

def test_bars():
    fig,ax=plt.subplots()
    bars=make_grouped_bar(ax,["A","B"],[[0.2,0.3],[0.4,0.6]],["X","Y"],annotate=True)
    assert len(bars)==2 and len(ax.texts)==4
    with pytest.raises(ValidationError):
        make_grouped_bar(ax,["A"],[[0.2]],["X"],yerr=[[0.1]])
    plt.close(fig)

def test_curves_do_not_fabricate_intervals():
    fig,ax=plt.subplots()
    with pytest.raises(ValidationError):
        make_learning_curves(ax,[1,2],[[0.1,0.2]],["X"],lower=[[0,0.1]],upper=[[0.2,0.3]])
    with pytest.raises(ValidationError):
        make_trend(ax,[1,2],[[0.1,0.2]],["X"],show_shadow=True)
    with pytest.raises(ValidationError):
        make_learning_curves(ax,[2,1],[[0.1,0.2]],["X"])
    lines=make_learning_curves(ax,[1,2],[[0.1,0.2]],["X"],lower=[[0,0.1]],
                          upper=[[0.2,0.3]],uncertainty_kind="ci")
    assert len(lines)==1
    plt.close(fig)

def test_heatmap_nan_policy():
    fig,ax=plt.subplots()
    with pytest.raises(ValidationError): make_heatmap(ax,[[1,np.nan]])
    with pytest.raises(ValidationError): make_heatmap(ax,[[1,2]],x_labels=["a"])
    assert make_heatmap(ax,[[1,np.nan]],allow_nan=True) is not None
    plt.close(fig)

def test_reliability_and_scatter():
    fig,ax=plt.subplots()
    with pytest.raises(ValidationError):
        make_reliability_diagram(ax,[0.5],[0.4],lower=[0.3],upper=[0.5])
    line=make_reliability_diagram(ax,[0.5,0.9],[0.4,0.8],
                      lower=[0.3,0.7],upper=[0.5,0.9],uncertainty_kind="ci")
    assert len(line.get_ydata())==2
    with pytest.raises(ValidationError): make_scatter(ax,[1],[2,3])
    plt.close(fig)
