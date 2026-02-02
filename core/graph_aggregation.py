"""
Graph Aggregation Module

Functions for aggregating spatiotemporal networks by community, municipality, or other groupings.
"""

import pandas as pd
import igraph as ig
from typing import Optional


def aggregate_graph_by_community_year(spatiotemporal_graph: ig.Graph) -> ig.Graph:
    """
    Aggregates a spatiotemporal graph where each node represents all nodes 
    with the same community membership in a given year.

    Args:
        spatiotemporal_graph: The input spatiotemporal graph with attributes:
            - Vertex: 'year', 'st_community', 'population', 'area', 
                     'centroid_x', 'centroid_y'
            - Edge: 'multi_count', 'mobility', and other numeric attributes

    Returns:
        An aggregated graph where nodes are (year, st_community) pairs
    """
    if not spatiotemporal_graph.vs:
        return ig.Graph(directed=spatiotemporal_graph.is_directed())

    # Prepare node DataFrame
    nodes_df = spatiotemporal_graph.get_vertex_dataframe()
    nodes_df['original_v_id'] = nodes_df.index

    # Define aggregation specifications
    agg_spec = {
        'population': 'sum',
        'area': 'sum',
        'centroid_x': 'mean',
        'centroid_y': 'mean',
        'original_v_id': 'count'
    }
    
    final_agg_spec = {k: v for k, v in agg_spec.items() if k in nodes_df.columns}
    if 'original_v_id' not in final_agg_spec:
        final_agg_spec['original_v_id'] = 'count'

    agg_nodes_df = nodes_df.groupby(['year', 'st_community']).agg(final_agg_spec).rename(
        columns={'original_v_id': 'original_node_count'}
    ).reset_index()

    # Create unique names for aggregated nodes
    agg_nodes_df['name'] = (agg_nodes_df['year'].astype(str) + '_' + 
                           agg_nodes_df['st_community'].astype(str))
    agg_nodes_df = agg_nodes_df[['name'] + [col for col in agg_nodes_df.columns if col != 'name']]

    # Prepare edge DataFrame
    edges_df = spatiotemporal_graph.get_edge_dataframe()
    
    # Map original vertex IDs to aggregated node names
    v_id_to_name_map = nodes_df.set_index('original_v_id')[['year', 'st_community']].apply(
        lambda r: f"{r.year}_{r.st_community}", axis=1
    )
    edges_df['source_name'] = edges_df['source'].map(v_id_to_name_map)
    edges_df['target_name'] = edges_df['target'].map(v_id_to_name_map)

    # Identify numeric edge attributes to sum
    numeric_edge_attrs = [
        attr for attr in edges_df.columns
        if pd.api.types.is_numeric_dtype(edges_df[attr]) and attr not in ['source', 'target']
    ]
    
    if not numeric_edge_attrs:
        agg_edges_df = edges_df.groupby(['source_name', 'target_name']).size().reset_index(name='weight')
    else:
        agg_edges_df = edges_df.groupby(['source_name', 'target_name'])[numeric_edge_attrs].sum().reset_index()

    # Create final graph
    final_graph = ig.Graph.DataFrame(
        edges=agg_edges_df,
        directed=spatiotemporal_graph.is_directed(),
        vertices=agg_nodes_df,
        use_vids=False
    )

    return final_graph


def aggregate_graph_by_gemeente_year(spatiotemporal_graph: ig.Graph) -> ig.Graph:
    """
    Aggregates a spatiotemporal graph by municipality (gemeente) and year.
    
    The gemeente is derived from the region code (first 4 digits of the 6-digit wijk code).

    Args:
        spatiotemporal_graph: The input spatiotemporal graph with attributes:
            - Vertex: 'year', 'region', 'population', 'area', 
                     'centroid_x', 'centroid_y', 'members', 'members_norm'
            - Edge: 'multi_count', 'mobility', 'distance', 'expected_edge_density'

    Returns:
        An aggregated graph where nodes are (year, gemeente) pairs
    """
    # Prepare node DataFrame
    nodes_df = spatiotemporal_graph.get_vertex_dataframe()
    nodes_df['gemeente'] = (nodes_df['region'] // 100).astype(int)
    nodes_df['original_v_id'] = nodes_df.index

    # Define aggregation specifications
    agg_spec = {
        'population': 'sum',
        'area': 'sum',
        'centroid_x': 'mean',
        'centroid_y': 'mean',
        'original_v_id': 'count',
        'members': 'sum',
        'members_norm': 'sum',
    }
    
    final_agg_spec = {k: v for k, v in agg_spec.items() if k in nodes_df.columns}
    if 'original_v_id' not in final_agg_spec:
        final_agg_spec['original_v_id'] = 'count'

    agg_nodes_df = nodes_df.groupby(['year', 'gemeente']).agg(final_agg_spec).rename(
        columns={'original_v_id': 'original_node_count'}
    ).reset_index()

    # Create unique names
    agg_nodes_df['name'] = (agg_nodes_df['year'].astype(str) + '_' + 
                           agg_nodes_df['gemeente'].astype(str))
    agg_nodes_df = agg_nodes_df[['name'] + [col for col in agg_nodes_df.columns if col != 'name']]

    # Prepare edge DataFrame
    edges_df = spatiotemporal_graph.get_edge_dataframe()
    
    v_id_to_name_map = nodes_df.set_index('original_v_id')[['year', 'gemeente']].apply(
        lambda r: f"{r.year}_{r.gemeente}", axis=1
    )
    edges_df['source_name'] = edges_df['source'].map(v_id_to_name_map)
    edges_df['target_name'] = edges_df['target'].map(v_id_to_name_map)

    # Aggregate edges
    numeric_edge_attrs = [
        attr for attr in edges_df.columns
        if pd.api.types.is_numeric_dtype(edges_df[attr]) and attr not in ['source', 'target']
    ]
    
    if not numeric_edge_attrs:
        agg_edges_df = edges_df.groupby(['source_name', 'target_name']).size().reset_index(name='weight')
    else:
        agg_edges_df = edges_df.groupby(['source_name', 'target_name'])[numeric_edge_attrs].sum().reset_index()

    # Create final graph
    final_graph = ig.Graph.DataFrame(
        edges=agg_edges_df,
        directed=spatiotemporal_graph.is_directed(),
        vertices=agg_nodes_df,
        use_vids=False
    )

    return final_graph
