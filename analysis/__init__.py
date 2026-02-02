"""
Analysis scripts for generating manuscript figures.

This package contains modules for:
- Network structure and aggregation visualizations
- Mixed membership analysis plots
- Diversity evolution and correlation plots
- Synthetic benchmark validation
"""

from . import network_analysis_plots
from . import mixed_membership_plots
from . import diversity_analysis_plots
from . import synthetic_benchmarks

__all__ = [
    'network_analysis_plots',
    'mixed_membership_plots',
    'diversity_analysis_plots',
    'synthetic_benchmarks'
]
