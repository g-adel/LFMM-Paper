"""
Utility functions for reproducible analysis.
Common data loading, preprocessing, and shared helpers.
"""

import igraph as ig
import numpy as np
import pandas as pd
import pickle
import os
import sys
from typing import Dict, List, Tuple, Optional, Any
import colorsys

# Add package modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(current_dir, 'core'))
sys.path.insert(0, os.path.join(current_dir, 'visualization'))
sys.path.insert(0, os.path.join(current_dir, 'analysis'))


# Community names
COMM_NAMES = [
    'Northern',                       # 0
    'Overijsel-aligned',              # 4
    'North Holland-aligned',          # 2
    'Utrecht-aligned',                # 5
    'Gelderland-aligned',             # 7
    'South Holland-aligned',          # 1
    'Brabant-aligned',                # 3
    'Zeeland-aligned',                # 8
    'Limburg-aligned',                # 6
]

# Color palette for communities
COMMUNITY_PALETTE = [colorsys.hls_to_rgb(h, 0.45, 1) 
                     for h in [0, .1, .17, .25, .5, .58, .7, .78, .88]]


def load_transverse_graph(filename: str = 'transverse_graph_wijk_CD_MM_cleaned.pkl') -> ig.Graph:
    """
    Load the main spatiotemporal graph.
    
    Args:
        filename: Name of the pickle file containing the graph
        
    Returns:
        igraph.Graph: The loaded spatiotemporal graph
    """
    # Try multiple possible locations
    possible_paths = [
        os.path.join(parent_dir, 'Mixed_membership', filename),
        os.path.join(parent_dir, 'Data', filename),
        os.path.join(current_dir, 'data', filename),
        filename  # Direct path if provided
    ]
    
    for filepath in possible_paths:
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                g = pickle.load(f)
            return g
    
    raise FileNotFoundError(f"Could not find {filename} in any expected location")


def load_urbanness_data(year: int = 2021) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load urbanness data for municipalities and neighborhoods.
    
    Args:
        year: Year for the urbanness data
        
    Returns:
        Tuple of (wijk_urbanness_df, gemeente_urbanness_df)
    """
    wijk_path = os.path.join(parent_dir, 'Data', 'cleanup', f'wijk_urbanness_{year}.csv')
    gemeente_path = os.path.join(parent_dir, 'Data', 'cleanup', f'gemeente_urbanness_{year}.csv')
    
    df_wijk = pd.read_csv(wijk_path, sep=';')
    df_gemeente = pd.read_csv(gemeente_path, sep=';')
    
    return df_wijk, df_gemeente


def ensure_output_dir(output_dir: str = 'Assets') -> str:
    """
    Ensure output directory exists.
    
    Args:
        output_dir: Name of the output directory
        
    Returns:
        Full path to the output directory
    """
    full_path = os.path.join(parent_dir, output_dir)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def get_yearly_graphs(g: ig.Graph, year_from: int = 2009, year_to: int = 2022) -> Dict[int, ig.Graph]:
    """
    Extract yearly graph snapshots from spatiotemporal graph.
    
    Args:
        g: Spatiotemporal graph
        year_from: Start year
        year_to: End year (exclusive)
        
    Returns:
        Dictionary mapping years to graph snapshots
    """
    import temporal_analysis
    return temporal_analysis.extract_yearly_graphs_no_type(g)


def aggregate_by_community_year(g: ig.Graph) -> ig.Graph:
    """
    Aggregate graph by community and year.
    
    Args:
        g: Spatiotemporal graph
        
    Returns:
        Aggregated graph
    """
    import graph_aggregation
    return graph_aggregation.aggregate_graph_by_community_year(g)


def aggregate_by_gemeente_year(g: ig.Graph) -> ig.Graph:
    """
    Aggregate graph by municipality (gemeente) and year.
    
    Args:
        g: Spatiotemporal graph
        
    Returns:
        Aggregated graph
    """
    import graph_aggregation
    return graph_aggregation.aggregate_graph_by_gemeente_year(g)


def calculate_density_matrix(adj_matrix: np.ndarray, populations: np.ndarray) -> np.ndarray:
    """
    Calculate density matrix by normalizing adjacency matrix by population products.
    
    Args:
        adj_matrix: Adjacency matrix
        populations: Population vector
        
    Returns:
        Density matrix
    """
    n = len(populations)
    density_matrix = np.zeros_like(adj_matrix, dtype=float)
    for i in range(n):
        for j in range(n):
            if populations[i] > 0 and populations[j] > 0:
                density_matrix[i, j] = adj_matrix[i, j] / (populations[i] * populations[j])
    return density_matrix


def calculate_gsi(membership_vector: np.ndarray) -> float:
    """
    Calculate Gini-Simpson Index from a membership vector.
    
    Args:
        membership_vector: Array of membership values
        
    Returns:
        Gini-Simpson Index (diversity measure)
    """
    total = np.sum(membership_vector)
    if total <= 0:
        return np.nan
    proportions = membership_vector / total
    return 1 - np.sum(proportions ** 2)


def weighted_avg(group: pd.DataFrame, avg_name: str, weight_name: str) -> float:
    """
    Calculate weighted average for a grouped DataFrame.
    
    Args:
        group: DataFrame group
        avg_name: Column name for values to average
        weight_name: Column name for weights
        
    Returns:
        Weighted average
    """
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan


def save_figure_and_pickle(fig, filename: str, output_dir: str = 'Assets', 
                           save_pickle: bool = True, dpi: int = 300):
    """
    Save matplotlib figure as PNG and optionally as pickle.
    
    Args:
        fig: Matplotlib figure object
        filename: Base filename (without extension)
        output_dir: Output directory name
        save_pickle: Whether to also save as pickle
        dpi: DPI for PNG output
    """
    import matplotlib.pyplot as plt
    
    output_path = ensure_output_dir(output_dir)
    
    # Save PNG
    png_path = os.path.join(output_path, f'{filename}.png')
    fig.savefig(png_path, dpi=dpi, bbox_inches='tight')
    print(f"Saved: {png_path}")
    
    # Save pickle if requested
    if save_pickle:
        pkl_path = os.path.join(output_path, f'{filename}.pkl')
        with open(pkl_path, 'wb') as f:
            pickle.dump(fig, f)
        print(f"Saved: {pkl_path}")


def get_n_communities(graphs: Dict[int, ig.Graph], year: int = 2009) -> int:
    """
    Get the number of communities from a yearly graph.
    
    Args:
        graphs: Dictionary of yearly graphs
        year: Year to check
        
    Returns:
        Number of communities
    """
    if 'members' in graphs[year].vs.attributes():
        return len(graphs[year].vs[0]['members'])
    elif 'st_community' in graphs[year].vs.attributes():
        return max(graphs[year].vs['st_community']) + 1
    else:
        raise ValueError("Cannot determine number of communities from graph")
