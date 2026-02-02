"""
Diversity analysis figures.
Generates Gini-Simpson Index evolution, statistical significance maps, and correlations.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from typing import Dict, Tuple
import os

from utils import (
    load_transverse_graph,
    load_urbanness_data,
    ensure_output_dir,
    save_figure_and_pickle,
    calculate_gsi,
    weighted_avg,
    get_yearly_graphs,
    COMM_NAMES
)


def calculate_diversity_by_region(g, year_from: int = 2009, year_to: int = 2022) -> Dict:
    """
    Calculate Gini-Simpson Index for each region over time.
    
    Args:
        g: Spatiotemporal graph
        year_from: Start year
        year_to: End year (exclusive)
        
    Returns:
        Dictionary mapping region_id -> {year -> GSI value}
    """
    import Mixed_membership.mixed_membership as mm
    
    # Get LFMM history
    LFMM_hist = mm.get_mmwf_history_by_region(g, 'members')
    
    # Extract yearly graphs
    graphs = get_yearly_graphs(g, year_from, year_to)
    
    # Calculate GSI for each region and year
    GSI_by_region = {}
    for region_id, region_data in LFMM_hist.items():
        GSI_by_region[region_id] = {}
        for year, year_data in region_data.items():
            if year >= year_from and year < year_to:
                gsi = calculate_gsi(year_data)
                GSI_by_region[region_id][year] = gsi
                
                # Store in vertex attribute
                try:
                    vertex = graphs[year].vs.find(region=region_id)
                    vertex['GSI'] = gsi
                except:
                    pass
    
    return GSI_by_region, graphs


def generate_gsi_evolution_plot(year_from: int = 2009, year_to: int = 2022,
                                output_dir: str = 'Assets'):
    """
    Generate plot showing evolution of Gini-Simpson Index over time.
    
    Args:
        year_from: Start year
        year_to: End year (exclusive)
        output_dir: Output directory
    """
    print("Generating Gini-Simpson Index Evolution plot...")
    
    g = load_transverse_graph()
    GSI_by_region, graphs = calculate_diversity_by_region(g, year_from, year_to)
    
    years = list(range(year_from, year_to))
    
    # Prepare data for box plots
    all_gsi_by_year = []
    weighted_means = []
    
    for year in years:
        year_gsi = []
        year_populations = []
        
        for region_id, year_dict in GSI_by_region.items():
            if year in year_dict:
                gsi_value = year_dict[year]
                if not np.isnan(gsi_value):
                    year_gsi.append(gsi_value)
                    # Get population for weighting
                    try:
                        vertex = graphs[year].vs.find(region=region_id)
                        year_populations.append(vertex['population'])
                    except:
                        year_populations.append(1)
        
        all_gsi_by_year.append(year_gsi)
        
        if len(year_gsi) > 0:
            weighted_mean = np.average(year_gsi, weights=year_populations)
            weighted_means.append(weighted_mean)
        else:
            weighted_means.append(np.nan)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Box plots
    bp = ax.boxplot(all_gsi_by_year, positions=years, widths=0.6, 
                    patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.6),
                    medianprops=dict(color='red', linewidth=2),
                    whiskerprops=dict(color='blue', linewidth=1.5),
                    capprops=dict(color='blue', linewidth=1.5),
                    whis=(5, 95))
    
    # Weighted mean line
    ax.plot(years, weighted_means, color='green', linestyle='--', 
           marker='d', linewidth=2, markersize=8, label='Weighted Mean')
    
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Gini-Simpson Index', fontsize=14)
    ax.set_title('Evolution of Gini-Simpson index over time', fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Tufte style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    filename = f'Evolution_of_Gini-Simpson_index_over_time'
    save_figure_and_pickle(fig, filename, output_dir, save_pickle=False)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


def generate_diversity_vs_urban_density(year: int = 2021, 
                                        output_dir: str = 'Assets'):
    """
    Generate scatter plot of diversity vs urban density.
    
    Args:
        year: Year to analyze
        output_dir: Output directory
    """
    print(f"Generating Diversity vs Urban Density plot for {year}...")
    
    # Load data
    g = load_transverse_graph()
    df_urbanness, GM_urbanness = load_urbanness_data(year)
    
    # Get graph for the year
    graphs = get_yearly_graphs(g, year, year + 1)
    g_year = graphs[year]
    
    # Merge graph attributes with urbanness data
    vertex_attributes_list = [v.attributes() for v in g_year.vs]
    graph_attributes_df = pd.DataFrame(vertex_attributes_list)
    
    df_urbanness = pd.merge(df_urbanness, graph_attributes_df, 
                           left_on='wijk', right_on='region', how='left')
    
    # Add gemeente column
    df_urbanness['gemeente'] = df_urbanness['wijk'] // 100
    df_urbanness = pd.merge(df_urbanness, GM_urbanness, on='gemeente', 
                           how='left', suffixes=('', '_GM'))
    
    # Calculate relative diversity
    df_calc = df_urbanness.dropna(subset=['GSI', 'GSI_GM', 'urban_density'])
    df_calc['rel_diversity'] = (df_calc['GSI'] - df_calc['GSI_GM']) / 0.108
    
    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    scatter = ax.scatter(df_calc['urban_density'], df_calc['rel_diversity'],
                        alpha=0.6, s=50, c='steelblue', edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('Urban Density', fontsize=14)
    ax.set_ylabel('Relative Diversity\n(Gini-Simpson Index)', fontsize=14)
    ax.set_title(f'Diversity vs Urban Density ({year})', fontsize=16)
    ax.grid(True, alpha=0.3)
    
    # Tufte style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    filename = 'Div_vs_Urban_Density'
    save_figure_and_pickle(fig, filename, output_dir)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


def generate_membership_composition(target_communities: list = [0, 4],
                                    year_from: int = 2009,
                                    year_to: int = 2022,
                                    output_dir: str = 'Assets'):
    """
    Generate stacked bar chart showing membership composition over time.
    
    Args:
        target_communities: List of community indices to analyze
        year_from: Start year
        year_to: End year (exclusive)
        output_dir: Output directory
    """
    target_comm_name = ' & '.join([COMM_NAMES[i] for i in target_communities])
    print(f"Generating Membership Composition for {target_comm_name}...")
    
    g = load_transverse_graph()
    graphs = get_yearly_graphs(g, year_from, year_to)
    n_comms = len(graphs[year_from].vs[0]['members'])
    
    years = list(range(year_from, year_to))
    
    # Collect membership data
    membership_composition = {i: [] for i in range(n_comms)}
    
    for year in years:
        # Calculate total members per community for this year
        year_totals = {i: 0 for i in range(n_comms)}
        
        for vertex in graphs[year].vs:
            max_community = np.argmax(vertex['members'])
            if max_community in target_communities:
                for i in range(n_comms):
                    year_totals[i] += vertex['members'][i]
        
        # Convert to fractions
        total_all = sum(year_totals.values())
        for i in range(n_comms):
            if total_all > 0:
                fraction = year_totals[i] / total_all
                membership_composition[i].append(fraction)
            else:
                membership_composition[i].append(0)
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 7))
    
    bottom = np.zeros(len(years))
    import igraph as ig
    palette = ig.ClusterColoringPalette(n_comms)
    
    for i in range(n_comms):
        fractions = np.array(membership_composition[i])
        ax.bar(years, fractions, bottom=bottom, 
              label=COMM_NAMES[i], color=palette[i], width=0.8)
        bottom += fractions
    
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Membership Fraction', fontsize=14)
    ax.set_title(f'Membership Composition in {target_comm_name} Regions', fontsize=16)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    
    filename = f'Membership_Composition_in_{target_comm_name.replace(" & ", "_")}_Regions'
    save_figure_and_pickle(fig, filename, output_dir, save_pickle=False)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


if __name__ == "__main__":
    # Generate all diversity figures
    generate_gsi_evolution_plot(year_from=2009, year_to=2022)
    generate_diversity_vs_urban_density(year=2021)
    generate_membership_composition(target_communities=[0, 4], year_from=2009, year_to=2022)
