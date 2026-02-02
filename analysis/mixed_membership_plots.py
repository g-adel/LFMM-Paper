"""
Mixed membership analysis figures.
Generates LFMM comparisons and municipality-level mixed membership visualizations.
"""

import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
import pickle
from typing import Dict, List
import os

from utils import (
    load_transverse_graph,
    aggregate_by_gemeente_year,
    ensure_output_dir,
    save_figure_and_pickle,
    COMM_NAMES
)


def generate_gemeente_network_visualization(year: int = 2021,
                                            method: str = 'CD',
                                            output_dir: str = 'Assets'):
    """
    Generate municipality-level network visualization.
    
    Args:
        year: Year to visualize
        method: 'CD' for community detection or 'MM' for mixed membership
        output_dir: Output directory
    """
    print(f"Generating GM_{method} network for {year}...")
    
    import Visualization.network_viz as nv
    
    # Load data
    g = load_transverse_graph()
    g_GM = aggregate_by_gemeente_year(g)
    
    # Extract year
    g_year = g_GM.subgraph(g_GM.vs.select(year=year))
    
    # Set community membership
    if method == 'CD':
        g_year.vs['st_community'] = [np.argmax(members) for members in g_year.vs['members']]
        membership_attr = 'st_community'
    else:  # MM
        membership_attr = None  # Will use mixed membership coloring
    
    # Create visual style
    import igraph as ig
    palette = ig.ClusterColoringPalette(len(COMM_NAMES))
    
    # Plot
    filename = f'GM_{method}_network_{year}.png'
    output_path = ensure_output_dir(output_dir)
    target_path = os.path.join(output_path, filename)
    
    plot = nv.plot_graph_with_style(
        g_year,
        weight_threshold=100,
        weight_attribute='multi_count',
        membership_attribute=membership_attr,
        vertex_size_scaling_factor=15.0,
        edge_width_scaling_factor=0.5,
        plot_bbox=(850, 1000),
        target=target_path,
        palette=palette,
        legend=True,
        comm_names=COMM_NAMES
    )
    
    print(f"✓ Generated {filename}")


def generate_mixed_membership_comparison(year: int = 2021,
                                        output_dir: str = 'Assets'):
    """
    Generate comparison of mixed membership at different aggregation levels.
    
    Args:
        year: Year to compare
        output_dir: Output directory
    """
    print(f"Generating Mixed Membership WK-GM comparison for {year}...")
    
    import Mixed_membership.mixed_membership as mm
    
    g = load_transverse_graph()
    
    # Get wijk-level graph
    g_wk = g.subgraph(g.vs.select(year=year))
    
    # Get gemeente-level graph
    g_GM = aggregate_by_gemeente_year(g)
    g_GM_year = g_GM.subgraph(g_GM.vs.select(year=year))
    
    # Calculate MMWF for both levels
    MMWF_wk = mm.link_fraction_mixed_membership(g_wk, 'multi_count')
    MMWF_GM = mm.link_fraction_mixed_membership(g_GM_year, 'multi_count')
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    n_comms = len(COMM_NAMES)
    import igraph as ig
    palette = ig.ClusterColoringPalette(n_comms)
    
    # Wijk-level
    wk_members = np.array([MMWF_wk[i] for i in range(len(MMWF_wk))])
    bottom_wk = np.zeros(len(MMWF_wk))
    
    for comm in range(n_comms):
        values = [m[comm] if len(m) > comm else 0 for m in wk_members]
        ax1.bar(range(len(values)), values, bottom=bottom_wk, 
               label=COMM_NAMES[comm], color=palette[comm])
        bottom_wk += values
    
    ax1.set_xlabel('Wijk Index', fontsize=12)
    ax1.set_ylabel('Mixed Membership Fraction', fontsize=12)
    ax1.set_title(f'Wijk-level Mixed Membership ({year})', fontsize=14)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    # Gemeente-level
    GM_members = np.array([MMWF_GM[i] for i in range(len(MMWF_GM))])
    bottom_GM = np.zeros(len(MMWF_GM))
    
    for comm in range(n_comms):
        values = [m[comm] if len(m) > comm else 0 for m in GM_members]
        ax2.bar(range(len(values)), values, bottom=bottom_GM,
               label=COMM_NAMES[comm], color=palette[comm])
        bottom_GM += values
    
    ax2.set_xlabel('Gemeente Index', fontsize=12)
    ax2.set_ylabel('Mixed Membership Fraction', fontsize=12)
    ax2.set_title(f'Gemeente-level Mixed Membership ({year})', fontsize=14)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    plt.tight_layout()
    
    filename = 'mixed_membership_WK_GM_comparison'
    save_figure_and_pickle(fig, filename, output_dir)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


if __name__ == "__main__":
    # Generate all mixed membership figures
    generate_gemeente_network_visualization(year=2021, method='CD')
    generate_gemeente_network_visualization(year=2021, method='MM')
    generate_mixed_membership_comparison(year=2021)
