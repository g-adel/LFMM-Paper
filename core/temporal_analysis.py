"""
Temporal Network Analysis Module

Functions for extracting and analyzing temporal slices and transitions in spatiotemporal networks.
"""

import igraph as ig
import numpy as np
from typing import Dict, Tuple


def extract_yearly_graphs_no_type(spatiotemporal_graph: ig.Graph) -> Dict[int, ig.Graph]:
    """
    Extracts individual yearly graphs from a combined spatiotemporal graph.

    Args:
        spatiotemporal_graph: The combined spatiotemporal graph with:
            - Vertex attributes: 'year' (required), 'region', other attributes
            - Edge attributes: 'multi_count' (for intra-year weight), 'mobility' (inter-year)

    Returns:
        Dictionary mapping years to undirected graphs for that year.
        Yearly graphs exclude 'year' and 'spatiotemporal_id' vertex attributes
        and 'mobility' edge attributes.
    """
    yearly_graphs_output = {}

    if not spatiotemporal_graph.vcount():
        return yearly_graphs_output

    if "year" not in spatiotemporal_graph.vertex_attributes():
        raise ValueError("Spatiotemporal graph is missing essential 'year' vertex attribute.")

    unique_years = sorted(list(set(spatiotemporal_graph.vs["year"])))
    st_vertex_years = spatiotemporal_graph.vs["year"]

    for year_val in unique_years:
        yearly_graph = ig.Graph(directed=False)

        # Select vertices for this year
        st_nodes_for_year_vs = spatiotemporal_graph.vs.select(year_eq=year_val)
        
        if not st_nodes_for_year_vs:
            yearly_graphs_output[year_val] = yearly_graph
            continue

        num_yearly_nodes = len(st_nodes_for_year_vs)
        yearly_graph.add_vertices(num_yearly_nodes)

        # Create mapping and copy vertex attributes
        st_original_idx_to_yearly_idx = {}
        for new_idx, st_vertex in enumerate(st_nodes_for_year_vs):
            st_original_idx_to_yearly_idx[st_vertex.index] = new_idx
            
            for attr_name, attr_value in st_vertex.attributes().items():
                # Exclude year and spatiotemporal_id
                if attr_name not in ("year", "spatiotemporal_id"): 
                    yearly_graph.vs[new_idx][attr_name] = attr_value
        
        # Identify and add intra-year edges
        edges_to_add_yearly = []
        edge_attributes_list_for_yearly_graph = [] 

        for st_edge in spatiotemporal_graph.es:
            source_node_idx = st_edge.source
            target_node_idx = st_edge.target

            # Check if both endpoints belong to current year
            if st_vertex_years[source_node_idx] == year_val and \
               st_vertex_years[target_node_idx] == year_val:
                
                if source_node_idx in st_original_idx_to_yearly_idx and \
                   target_node_idx in st_original_idx_to_yearly_idx:
                    
                    yearly_source_idx = st_original_idx_to_yearly_idx[source_node_idx]
                    yearly_target_idx = st_original_idx_to_yearly_idx[target_node_idx]
                    
                    edges_to_add_yearly.append((yearly_source_idx, yearly_target_idx))
                    
                    current_edge_attrs_for_yearly = {}
                    for st_attr_name, st_attr_value in st_edge.attributes().items():
                        if st_attr_name == "mobility":
                            continue  # Skip mobility for intra-year edges
                        current_edge_attrs_for_yearly[st_attr_name] = st_attr_value
                    edge_attributes_list_for_yearly_graph.append(current_edge_attrs_for_yearly)

        if edges_to_add_yearly:
            yearly_graph.add_edges(edges_to_add_yearly)
            
            if edge_attributes_list_for_yearly_graph:
                all_edge_attr_keys = set()
                for attrs_dict in edge_attributes_list_for_yearly_graph:
                    all_edge_attr_keys.update(attrs_dict.keys())
                
                for key in all_edge_attr_keys:
                    attr_values_for_key = [attrs.get(key) for attrs in edge_attributes_list_for_yearly_graph]
                    yearly_graph.es[key] = attr_values_for_key
        
        yearly_graphs_output[year_val] = yearly_graph
        
    return yearly_graphs_output


def extract_interlayer_graphs(spatiotemporal_graph: ig.Graph) -> Dict[Tuple[int, int], ig.Graph]:
    """
    Extracts bipartite graphs of interlayer edges between consecutive years.

    Args:
        spatiotemporal_graph: The combined spatiotemporal graph with:
            - Vertex attributes: 'year' (required)
            - Edge attributes: 'mobility' (for interlayer edges)

    Returns:
        Dictionary mapping (year1, year2) tuples to bipartite graphs.
        Vertices have a 'type' attribute (False for year1, True for year2).
    """
    interlayer_graphs_output = {}

    if not spatiotemporal_graph.vcount():
        return interlayer_graphs_output

    if "year" not in spatiotemporal_graph.vertex_attributes():
        raise ValueError("Spatiotemporal graph is missing essential 'year' vertex attribute.")

    unique_years = sorted(list(set(spatiotemporal_graph.vs["year"])))
    st_vertex_years = spatiotemporal_graph.vs["year"]

    for i in range(len(unique_years) - 1):
        year1 = unique_years[i]
        year2 = unique_years[i + 1]
        
        interlayer_graph = ig.Graph(directed=spatiotemporal_graph.is_directed())
        
        # Select vertices from both years
        st_nodes_year1_vs = spatiotemporal_graph.vs.select(year_eq=year1)
        st_nodes_year2_vs = spatiotemporal_graph.vs.select(year_eq=year2)

        if not st_nodes_year1_vs or not st_nodes_year2_vs:
            interlayer_graphs_output[(year1, year2)] = interlayer_graph
            continue

        # Create mapping
        st_original_idx_to_new_idx = {}
        
        for new_idx, st_vertex in enumerate(st_nodes_year1_vs):
            st_original_idx_to_new_idx[st_vertex.index] = new_idx
        
        offset = len(st_nodes_year1_vs)
        for new_idx, st_vertex in enumerate(st_nodes_year2_vs):
            st_original_idx_to_new_idx[st_vertex.index] = new_idx + offset

        all_st_vertices = list(st_nodes_year1_vs) + list(st_nodes_year2_vs)
        interlayer_graph.add_vertices(len(all_st_vertices))
        
        # Set bipartite types
        types = [False] * len(st_nodes_year1_vs) + [True] * len(st_nodes_year2_vs)
        interlayer_graph.vs["type"] = types
        
        # Copy vertex attributes
        for new_idx, st_vertex in enumerate(all_st_vertices):
            for attr, val in st_vertex.attributes().items():
                if attr not in ("year", "spatiotemporal_id"):
                    interlayer_graph.vs[new_idx][attr] = val
            interlayer_graph.vs[new_idx]["original_year"] = st_vertex["year"]

        # Add interlayer edges
        edges_to_add = []
        edge_attributes_list = []

        st_edges = spatiotemporal_graph.es.select(_source_in=st_nodes_year1_vs, 
                                                  _target_in=st_nodes_year2_vs)
        
        for st_edge in st_edges:
            source_idx = st_edge.source
            target_idx = st_edge.target
            
            if st_vertex_years[source_idx] == year1 and st_vertex_years[target_idx] == year2:
                new_source = st_original_idx_to_new_idx[source_idx]
                new_target = st_original_idx_to_new_idx[target_idx]
                edges_to_add.append((new_source, new_target))
                edge_attributes_list.append(st_edge.attributes())

        if edges_to_add:
            interlayer_graph.add_edges(edges_to_add)
            
            if edge_attributes_list:
                all_edge_attr_keys = set()
                for attrs_dict in edge_attributes_list:
                    all_edge_attr_keys.update(attrs_dict.keys())
                
                for key in all_edge_attr_keys:
                    attr_values = [attrs.get(key) for attrs in edge_attributes_list]
                    interlayer_graph.es[key] = attr_values

        interlayer_graphs_output[(year1, year2)] = interlayer_graph

    return interlayer_graphs_output


def get_contingency_matrix(bipartite_graph: ig.Graph, attribute: str = 'weight') -> np.ndarray:
    """
    Creates a contingency matrix from a bipartite graph.
    
    Args:
        bipartite_graph: A bipartite graph with 'type' vertex attribute
        attribute: Edge attribute to use for weights
        
    Returns:
        Contingency matrix where rows represent type=False nodes 
        and columns represent type=True nodes
    """
    if 'type' not in bipartite_graph.vs.attributes():
        raise ValueError("Graph must have 'type' vertex attribute")
    
    # Get nodes of each type
    type_false_nodes = [v.index for v in bipartite_graph.vs if not v['type']]
    type_true_nodes = [v.index for v in bipartite_graph.vs if v['type']]
    
    n_rows = len(type_false_nodes)
    n_cols = len(type_true_nodes)
    
    contingency = np.zeros((n_rows, n_cols))
    
    # Fill the matrix
    for edge in bipartite_graph.es:
        source = edge.source
        target = edge.target
        weight = edge[attribute] if attribute in edge.attributes() else 1
        
        if source in type_false_nodes and target in type_true_nodes:
            row_idx = type_false_nodes.index(source)
            col_idx = type_true_nodes.index(target)
            contingency[row_idx, col_idx] = weight
        elif target in type_false_nodes and source in type_true_nodes:
            row_idx = type_false_nodes.index(target)
            col_idx = type_true_nodes.index(source)
            contingency[row_idx, col_idx] = weight
    
    return contingency
