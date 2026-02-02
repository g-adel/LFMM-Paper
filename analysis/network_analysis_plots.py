"""
Network visualization figures.
Generates community-aggregated network visualizations and density matrices.
"""

import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as patches
import pickle
from typing import List, Optional, Tuple
import os

from utils import (
    load_transverse_graph, 
    aggregate_by_community_year,
    aggregate_by_gemeente_year,
    ensure_output_dir,
    save_figure_and_pickle,
    calculate_density_matrix,
    COMM_NAMES,
    COMMUNITY_PALETTE
)


def adj_density_fig(density_matrix: np.ndarray, 
                    comm_names: List[str], 
                    populations: np.ndarray, 
                    title: Optional[str] = "Community-Aggregated Network Density", 
                    filename: Optional[str] = None,
                    output_dir: str = 'Assets',
                    use_palette: bool = True,
                    palette: Optional[List] = None):
    """
    Creates a figure representing the density matrix of community interactions.

    Args:
        density_matrix: The n x n matrix of interaction densities
        comm_names: List of names for the n communities
        populations: Array of population sizes for each community
        title: The title for the plot
        filename: If provided, the filename to save the figure
        output_dir: Output directory for saving
        use_palette: Whether to use colored diagonal blocks
        palette: Color palette for diagonal blocks
    """
    if palette is None:
        palette = COMMUNITY_PALETTE
        
    n_communities = density_matrix.shape[0]

    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')

    # Normalize populations to get proportional widths and heights
    pop_fractions = populations / np.sum(populations)
    x_coords = np.concatenate(([0], np.cumsum(pop_fractions)))
    y_coords = np.concatenate(([0], np.cumsum(pop_fractions)))

    # Create colormap for off-diagonal elements
    if use_palette:
        cmap = plt.cm.colors.LinearSegmentedColormap.from_list(
            'grey_scaled', plt.get_cmap('Greys')(np.linspace(0, 0.9, 256)))
    else:
        cmap = plt.get_cmap('Blues')

    # Get valid (non-diagonal) density values for normalization
    valid_density_values = density_matrix[~np.eye(n_communities, dtype=bool)]
    if len(valid_density_values) > 0:
        norm = mcolors.Normalize(vmin=np.min(valid_density_values), 
                                 vmax=np.max(valid_density_values))
    else:
        norm = mcolors.Normalize(vmin=0, vmax=1)

    for i in range(n_communities):
        for j in range(n_communities):
            x = x_coords[j]
            y = y_coords[i]
            width = pop_fractions[j]
            height = pop_fractions[i]
            density = density_matrix[i, j]

            # Set diagonal blocks to palette colors or black
            if i == j:
                color = palette[i] if use_palette else 'black'
            else:
                color = cmap(norm(density))

            rect = patches.Rectangle((x, y), width, height, linewidth=1, 
                                    edgecolor='white', facecolor=color)
            ax.add_patch(rect)

    # Customize axes and labels
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.invert_yaxis()

    ax.set_xticks(x_coords[:-1] + pop_fractions / 2)
    ax.set_yticks(y_coords[:-1] + pop_fractions / 2)
    ax.set_xticklabels(comm_names, rotation=45, fontsize=15)
    ax.set_yticklabels(comm_names, rotation=45, fontsize=15)

    # Add color bar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=13)
    cbar.set_label('Edge Density (Off-diagonal Elements)', rotation=270, 
                   labelpad=20, fontsize=15)

    # Add density values as text
    for i in range(n_communities):
        for j in range(n_communities):
            text_x = x_coords[j] + pop_fractions[j] / 2
            text_y = y_coords[i] + pop_fractions[i] / 2
            density_value = density_matrix[i, j]
            density_text = f'{density_value:.1e}'.replace('e-0', 'e-')

            # Determine text color
            if i == j and use_palette:
                r, g, b = palette[i]
                brightness = 0.299*r + 0.587*g + 0.114*b
                text_color = 'white' if brightness < 0.5 else 'black'
            else:
                color_intensity = norm(density_value) if len(valid_density_values) > 0 else 0.5
                text_color = 'white' if color_intensity > 0.5 else 'black'

            ax.text(text_x, text_y, density_text, 
                   ha='center', va='center', 
                   color=text_color, fontsize=11, fontweight='bold')

    plt.tight_layout()
    
    if filename:
        save_figure_and_pickle(fig, filename, output_dir)
    
    return fig


def generate_community_aggregated_network(year: int = 2021, 
                                          output_dir: str = 'Assets'):
    """
    Generate the community-aggregated network density figure.
    
    Args:
        year: Year to generate the figure for
        output_dir: Output directory
    """
    print(f"Generating Community-Aggregated Network for {year}...")
    
    # Load and process data
    g = load_transverse_graph()
    comm_g = aggregate_by_community_year(g)
    
    # Extract yearly graphs
    import Transverse_network.transverse_graphs as tg
    comm_gs = tg.extract_yearly_graphs_no_type(comm_g)
    
    # Get data for specified year
    graph = comm_gs[year]
    n_communities = max(graph.vs['st_community']) + 1
    
    # Get adjacency matrix and populations
    adj_matrix = np.array(graph.get_adjacency(attribute='multi_count').data)
    populations = np.array(graph.vs['population'])
    
    # Calculate density matrix
    density_matrix = calculate_density_matrix(adj_matrix, populations)
    
    # Generate figure
    filename = f'Community-Aggregated_Network_{year}'
    fig = adj_density_fig(
        density_matrix=density_matrix,
        comm_names=COMM_NAMES,
        populations=populations,
        filename=filename,
        output_dir=output_dir,
        use_palette=True
    )
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


def generate_rgb_composite_connection_types(year: int = 2021,
                                            output_dir: str = 'Assets'):
    """
    Generate RGB composite visualization of connection types.
    
    Args:
        year: Year to generate the figure for
        output_dir: Output directory
    """
    print(f"Generating RGB Composite of Connection Types for {year}...")
    
    # Load and process data
    g = load_transverse_graph()
    comm_g = aggregate_by_community_year(g)
    
    import Transverse_network.transverse_graphs as tg
    comm_gs = tg.extract_yearly_graphs_no_type(comm_g)
    
    graph = comm_gs[year]
    n_communities = max(graph.vs['st_community']) + 1
    
    # Get adjacency matrices by connection type
    family_adj = np.array(graph.get_adjacency(attribute='family_count').data)
    colleague_adj = np.array(graph.get_adjacency(attribute='colleague_count').data)
    school_adj = np.array(graph.get_adjacency(attribute='school_count').data)
    total_adj = family_adj + colleague_adj + school_adj
    
    # Calculate fractions
    with np.errstate(divide='ignore', invalid='ignore'):
        family_frac = np.nan_to_num(family_adj / total_adj)
        colleague_frac = np.nan_to_num(colleague_adj / total_adj)
        school_frac = np.nan_to_num(school_adj / total_adj)
    
    # Create RGB matrix
    rgb_matrix = np.zeros((n_communities, n_communities, 3))
    rgb_matrix[..., 0] = family_frac    # Red channel
    rgb_matrix[..., 1] = colleague_frac # Green channel
    rgb_matrix[..., 2] = school_frac    # Blue channel
    
    # Plotting
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.imshow(rgb_matrix)
    
    # Add fraction text
    for i in range(n_communities):
        for j in range(n_communities):
            label = (f"{family_frac[i, j]:.2f}\n"
                    f"{colleague_frac[i, j]:.2f}\n"
                    f"{school_frac[i, j]:.2f}")
            
            brightness = 0.299*rgb_matrix[i, j, 0] + 0.587*rgb_matrix[i, j, 1] + 0.114*rgb_matrix[i, j, 2]
            text_color = 'black' if brightness > 0.5 else 'white'
            
            ax.text(j, i, label, ha='center', va='center', 
                   color=text_color, fontsize=11, fontweight='bold')
    
    # Set labels
    ax.set_xticks(np.arange(n_communities))
    ax.set_yticks(np.arange(n_communities))
    ax.set_xticklabels(COMM_NAMES, rotation=90)
    ax.set_yticklabels(COMM_NAMES)
    ax.tick_params(axis="x", bottom=True, top=False, labelbottom=True, labeltop=False)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', label='Family (R)'),
        Patch(facecolor='green', label='Colleague (G)'),
        Patch(facecolor='blue', label='School (B)'),
        Patch(facecolor=(.5, .5, 0), label='Family + Colleague'),
        Patch(facecolor=(0, .5, .5), label='Colleague + School'),
        Patch(facecolor=(.5, 0, .5), label='Family + School'),
        Patch(facecolor=(.33, .33, .33), label='All Three Equal'),
    ]
    ax.legend(handles=legend_elements, bbox_to_anchor=(1.025, 1), 
             loc='upper left', title="Connection Mix")
    
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    
    filename = f'RGB_Composite_Connection_Types_{year}'
    save_figure_and_pickle(fig, filename, output_dir, save_pickle=False)
    
    plt.close(fig)
    print(f"✓ Generated {filename}")


if __name__ == "__main__":
    # Generate all network figures
    generate_community_aggregated_network(year=2021)
    generate_rgb_composite_connection_types(year=2021)
