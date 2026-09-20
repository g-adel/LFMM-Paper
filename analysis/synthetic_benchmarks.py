"""
Synthetic benchmark figures.
Generates LFMM synthetic benchmark and parameter space heatmap figures.
"""

import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
from typing import Tuple
import os

from utils import ensure_output_dir, save_figure_and_pickle


def generate_sbm_data(N: int, n_agg_sets: int, mu: float, 
                      avg_deg: int = 20, agg_noise: float = 0.0) -> Tuple[ig.Graph, np.ndarray]:
    """
    Generates SBM and mapping with specific noise level.
    
    Args:
        N: Number of nodes
        n_agg_sets: Number of aggregation sets
        mu: Affinity parameter (fraction of edges between communities)
        avg_deg: Average degree
        agg_noise: Aggregation intermixedness parameter
        
    Returns:
        Tuple of (individual graph, mapping array)
    """
    n_comm = 2
    block_sizes = [N // n_comm] * n_comm
    
    k_out = mu * avg_deg
    k_in = (1 - mu) * avg_deg
    
    p_out = k_out / (N / 2)
    p_in = k_in / (N / 2)
    
    pref_matrix = [[p_in, p_out], [p_out, p_in]]
    g_ind = ig.Graph.SBM(N, pref_matrix, block_sizes, directed=False)    

    # Ground Truth
    ground_truth = np.concatenate([[i]*size for i, size in enumerate(block_sizes)])
    g_ind.vs["ground_truth"] = ground_truth

    # Generate Mapping
    mapping = np.zeros(N, dtype=int) 
    
    # Vectorized decision for noise vs spatial
    random_mask = np.random.rand(N) < agg_noise
    
    # Spatial indices (linear mapping)
    spatial_indices = np.floor((np.arange(N) / N) * n_agg_sets).astype(int)
    spatial_indices = np.clip(spatial_indices, 0, n_agg_sets - 1)
    
    # Random indices
    random_indices = np.random.randint(0, n_agg_sets, size=N)
    
    # Combine based on mask
    mapping = np.where(random_mask, random_indices, spatial_indices)
    
    g_ind.vs["agg_id"] = mapping
    return g_ind, mapping


def aggregate_network(g: ig.Graph, mapping: np.ndarray) -> ig.Graph:
    """
    Aggregates graph based on mapping.
    
    Args:
        g: Individual-level graph
        mapping: Node to aggregate set mapping
        
    Returns:
        Aggregated graph
    """
    n_agg_nodes = max(mapping) + 1
    
    # Edge Aggregation
    edge_weights = {}
    for e in g.es:
        u, v = e.tuple
        set_u, set_v = mapping[u], mapping[v]
        if set_u > set_v:
            set_u, set_v = set_v, set_u
        key = (set_u, set_v)
        edge_weights[key] = edge_weights.get(key, 0) + 1
    
    edges = list(edge_weights.keys())
    weights = list(edge_weights.values())
    
    g_agg = ig.Graph(n_agg_nodes, edges, directed=False)
    g_agg.es["weight"] = weights
    return g_agg


def get_aggregate_ground_truth(g_ind: ig.Graph, mapping: np.ndarray, 
                               n_agg_sets: int) -> np.ndarray:
    """
    Determines label of aggregate set via majority vote.
    
    Args:
        g_ind: Individual-level graph
        mapping: Node to aggregate set mapping
        n_agg_sets: Number of aggregate sets
        
    Returns:
        Array of community labels for aggregate sets
    """
    agg_labels = np.zeros(n_agg_sets, dtype=int)
    votes = np.zeros((n_agg_sets, 2))  # Assuming 2 communities
    
    node_gt = np.array(g_ind.vs["ground_truth"])
    
    for agg_id, comm_id in zip(mapping, node_gt):
        votes[agg_id, comm_id] += 1
        
    agg_labels = np.argmax(votes, axis=1)
    return agg_labels


def compute_lfmm_minority(g_agg: ig.Graph, partition_gt: np.ndarray) -> float:
    """
    Computes LFMM and returns the average minority fraction.
    
    Args:
        g_agg: Aggregated graph
        partition_gt: Ground truth partition
        
    Returns:
        Average minority fraction
    """
    n_nodes = g_agg.vcount()
    n_comms = 2
    
    M = np.zeros((n_nodes, n_comms))
    
    # Build membership matrix M
    for edge in g_agg.es:
        u, v = edge.tuple
        w = edge["weight"]
        
        comm_u = partition_gt[u]
        comm_v = partition_gt[v]
        
        if u == v:
            # Aggregation stores each internal edge once; count both endpoints.
            M[u, comm_u] += 2 * w
        else:
            M[u, comm_v] += w
            M[v, comm_u] += w
    
    # Normalize
    row_sums = M.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    M_norm = M / row_sums
    
    # Calculate minority fraction
    minorities = []
    for i in range(n_nodes):
        gt_comm = partition_gt[i]
        maj_frac = M_norm[i, gt_comm]
        minorities.append(1.0 - maj_frac)
        
    return np.mean(minorities)


def generate_lfmm_synthetic_heatmap(output_dir: str = 'Assets'):
    """
    Generate LFMM synthetic parameter space heatmap.
    
    Args:
        output_dir: Output directory
    """
    print("Generating LFMM Synthetic Heatmap (this may take a while)...")
    
    # Parameters
    N = 1000
    n_agg_sets = 50
    grid_res = 25
    n_trials = 10
    sigma_smooth = 1.0
    
    mu_range = np.linspace(0.0, 0.5, grid_res)
    noise_range = np.linspace(0.0, 1.0, grid_res)
    
    Z = np.zeros((grid_res, grid_res))
    
    print(f"Running simulation: {grid_res}x{grid_res} grid, {n_trials} trials per point...")
    
    # Grid search
    for i, noise_prob in enumerate(noise_range):
        if i % 5 == 0:
            print(f"  Processing row {i}/{grid_res} (Noise={noise_prob:.2f})...")
        
        for j, mu in enumerate(mu_range):
            trial_results = []
            
            for _ in range(n_trials):
                g_ind, mapping = generate_sbm_data(N, n_agg_sets, mu, agg_noise=noise_prob)
                g_agg = aggregate_network(g_ind, mapping)
                part_gt = get_aggregate_ground_truth(g_ind, mapping, n_agg_sets)
                val = compute_lfmm_minority(g_agg, part_gt)
                trial_results.append(val)
            
            Z[i, j] = np.mean(trial_results)
    
    # Smooth the data
    Z_smooth = gaussian_filter(Z, sigma=sigma_smooth)
    
    # Plot
    X, Y = np.meshgrid(mu_range, noise_range)
    
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Background heatmap
    cf = ax.contourf(X, Y, Z_smooth, levels=20, alpha=0.75)
    
    # Isolines
    levels = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45])
    cs = ax.contour(X, Y, Z_smooth, levels=levels, colors='black', linewidths=1.75)
    
    # Annotations
    ax.clabel(cs, inline=True, fontsize=13, fmt='%.2f', colors='black')
    
    # Styling
    ax.set_xlabel("Affinity Parameter ($\\mu$)", fontsize=13)
    ax.set_ylabel("Aggregation intermixedness ($m$)", fontsize=13)
    ax.tick_params(labelsize=11)
    
    # Colorbar
    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label('LFMM mean value', fontsize=13)
    cbar.ax.tick_params(labelsize=10)
    cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2f}'))
    
    plt.tight_layout()
    
    filename = 'LFMM_synthetic_heatmap'
    save_figure_and_pickle(fig, filename, output_dir, save_pickle=False, dpi=600)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


def generate_lfmm_synthetic_benchmark(output_dir: str = 'Assets'):
    """
    Generate LFMM synthetic benchmark comparison figure.
    
    Args:
        output_dir: Output directory
    """
    print("Generating LFMM Synthetic Benchmark...")
    
    # This is a placeholder - the actual implementation would require
    # the full benchmark code from synthetic.py
    # For now, we'll create a simple placeholder
    
    print("⚠ LFMM Synthetic Benchmark requires full implementation from synthetic.py")
    print("  Please refer to Mixed_membership/synthetic.py for the complete code")


if __name__ == "__main__":
    # Generate synthetic figures
    generate_lfmm_synthetic_heatmap()
    # generate_lfmm_synthetic_benchmark()  # Uncomment when fully implemented
