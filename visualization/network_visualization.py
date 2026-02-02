"""
Network Visualization Module

Core functions for visualizing spatial network graphs with community structure.
"""

import igraph as ig
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches
import os
from typing import Tuple, Any, Optional, List
from IPython.display import Image, display


def get_vertex_colors(vis_g: ig.Graph, membership_attribute: str, 
                     default_vertex_color: str, inter_community_edge_color: str,
                     weight_attr: str, palette):
    """
    Calculate vertex and edge colors based on community membership.
    
    Args:
        vis_g: Graph to color
        membership_attribute: Vertex attribute containing community membership
        default_vertex_color: Default color for vertices
        inter_community_edge_color: Color for edges between communities
        weight_attr: Edge attribute for weights
        palette: Color palette for communities
        
    Returns:
        Tuple of (vertex_colors, edge_colors, edge_widths)
    """
    memberships = vis_g.vs[membership_attribute]
    
    # Vertex colors
    vertex_colors = [palette[m] for m in memberships]

    # Edge colors
    edge_colors_list = []
    for edge in vis_g.es:
        source_comm = memberships[edge.source]
        target_comm = memberships[edge.target]
        if source_comm is not None and source_comm == target_comm:
            edge_colors_list.append(palette[source_comm])
        else:
            edge_colors_list.append(inter_community_edge_color)

    # Edge widths based on weights
    edge_widths = [1.0] * vis_g.ecount()
    if vis_g.ecount() > 0 and weight_attr in vis_g.es.attributes():
        weights = np.array(vis_g.es[weight_attr])
        max_weight = weights.max()
        if max_weight > 0:
            safe_weights = np.maximum(weights, 0)
            edge_widths = np.power(safe_weights / max_weight, 0.65)

    return vertex_colors, edge_colors_list, edge_widths


def plot_graph_with_style(
    g: ig.Graph,
    weight_threshold: float = 1000.0,
    weight_attribute: str = 'weight',
    population_attribute: str = 'population',
    centroid_x_attribute: str = 'centroid_x',
    centroid_y_attribute: str = 'centroid_y',
    membership_attribute: Optional[str] = None,
    vertex_size_scaling_factor: float = 10.0,
    edge_width_scaling_factor: float = 1.5,
    plot_bbox: Tuple[int, int] = (850, 1000),
    plot_margin: int = 20,
    default_vertex_color: str = "darkblue",
    inter_community_edge_color: str = "black",
    target: Optional[Any] = None,
    palette = None,
    legend: bool = False,
    comm_names: Optional[List[str]] = None,
) -> Optional[Any]:
    """
    Plot a network graph with community-based styling.

    Args:
        g: Input graph
        weight_threshold: Minimum edge weight to include
        weight_attribute: Edge attribute for weights
        population_attribute: Vertex attribute for population (determines size)
        centroid_x_attribute, centroid_y_attribute: Vertex attributes for layout
        membership_attribute: Vertex attribute for community membership
        vertex_size_scaling_factor: Scale factor for vertex sizes
        edge_width_scaling_factor: Scale factor for edge widths
        plot_bbox: (width, height) tuple for plot area
        plot_margin: Margin around plot
        default_vertex_color: Color when no membership info
        inter_community_edge_color: Color for inter-community edges
        target: File path to save, or None
        palette: Color palette for communities
        legend: Whether to add legend
        comm_names: Community names for legend

    Returns:
        Plot object or None
    """
    if g.vcount() == 0:
        return None

    # Filter graph
    vis_g = g.copy()
    edges_to_delete = [
        edge.index for edge in vis_g.es
        if (weight_attribute in edge.attributes() and 
            edge[weight_attribute] < weight_threshold) or 
           edge.source == edge.target
    ]
    if edges_to_delete:
        vis_g.delete_edges(edges_to_delete)

    # Keep largest component
    if vis_g.vcount() > 0 and vis_g.ecount() > 0:
        components = vis_g.components(mode='weak')
        if len(components) > 1:
            vis_g = components.giant()

    if vis_g.vcount() == 0:
        return None

    # Generate layout
    coords_x = vis_g.vs[centroid_x_attribute]
    coords_y = vis_g.vs[centroid_y_attribute]
    coords_np = np.array(list(zip(coords_x, coords_y)), dtype=float)
    coords_np[:, 1] = -coords_np[:, 1]
    coords_np[:, 0] = coords_np[:, 0] * 2
    final_layout = ig.Layout(coords=coords_np.tolist())

    # Vertex sizes
    vertex_sizes = [5.0] * vis_g.vcount()
    if population_attribute in vis_g.vs.attributes():
        populations = np.array(vis_g.vs[population_attribute], dtype=float)
        populations = np.maximum(np.nan_to_num(populations), 0)
        max_pop = populations.max()
        if max_pop > 0:
            vertex_sizes = np.power(populations / max_pop, 0.3) * vertex_size_scaling_factor
            vertex_sizes = np.maximum(vertex_sizes, 1.0)

    # Colors
    if membership_attribute is not None and membership_attribute in vis_g.vs.attributes():
        vertex_colors, edge_colors, edge_widths = get_vertex_colors(
            vis_g, membership_attribute, default_vertex_color,
            inter_community_edge_color, weight_attribute, palette
        )
    else:
        vertex_colors = [default_vertex_color] * vis_g.vcount()
        edge_colors = [inter_community_edge_color] * vis_g.ecount()
        edge_widths = [1.0] * vis_g.ecount()

    # Visual style
    visual_style = {
        "edge_width": np.array(edge_widths) * edge_width_scaling_factor,
        "vertex_size": vertex_sizes,
        "vertex_label": None,
        "edge_arrow_size": 0,
        "layout": final_layout,
        "bbox": plot_bbox,
        "margin": plot_margin,
        "vertex_color": vertex_colors,
        "edge_color": edge_colors,
        "vertex_frame_color": (0.5, 0.5, 0.5, 0.5),
        "vertex_frame_width": 0.7,
    }

    # Plot with optional legend
    if legend and palette is not None:
        temp_ig_filename = "temp_ig_plot.png"
        ig.plot(vis_g, target=temp_ig_filename, **visual_style)
        
        dpi = 100
        fig, ax = plt.subplots(figsize=(plot_bbox[0]/dpi, plot_bbox[1]/dpi))
        
        if os.path.exists(temp_ig_filename):
            img = plt.imread(temp_ig_filename)
            ax.imshow(img)
            ax.axis('off')
            os.remove(temp_ig_filename)
        
        from matplotlib.lines import Line2D
        if comm_names:
            legend_elements = [
                Line2D([0], [0], marker='s', color='w',
                      label=f'{comm_names[i]}',
                      markerfacecolor=palette[i], markersize=12)
                for i in range(len(comm_names))
            ]
            ax.legend(handles=legend_elements, loc='upper left', 
                     fontsize=12, frameon=False)
        
        plt.tight_layout()
        if target:
            plt.savefig(target, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            return None
        return fig

    # Simple plot without legend
    if target:
        return ig.plot(vis_g, target=target, **visual_style)
    else:
        temp_file = 'temp_plot.png'
        ig.plot(vis_g, target=temp_file, **visual_style)
        display(Image(temp_file))
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return None
