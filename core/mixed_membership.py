"""
Mixed Membership Analysis Module

Implements Link Fraction Mixed Membership (LFMM) algorithm
for computing node-level mixed membership in community-structured networks.
"""

import igraph as ig
import numpy as np
from typing import Dict, List


def mixed_membership_link_weight(st_g: ig.Graph, inter_attr: str, 
                                  comm_attr: str = 'st_community') -> List[np.ndarray]:
    """
    Compute mixed-membership vector for each node by summing edge weights to each community.

    Parameters:
    -----------
    st_g : igraph.Graph
        The spatiotemporal graph
    inter_attr : str
        The name of the edge attribute containing the inter-community weights
    comm_attr : str
        The name of the vertex attribute containing community membership
        
    Returns:
    --------
    List[np.ndarray]
        List of mixed membership vectors, one per vertex
    """
    communities = list(set(st_g.vs[comm_attr]))
    communities.sort()

    mixed_membership_vectors = []

    for node_idx in range(len(st_g.vs)):
        membership_vector = np.zeros(len(communities))
        
        incident_edges = st_g.incident(node_idx)
        
        for edge_idx in incident_edges:
            edge = st_g.es[edge_idx]
            other_node_idx = edge.target if edge.source == node_idx else edge.source
            other_community = st_g.vs[other_node_idx][comm_attr]
            
            weight = edge[inter_attr]
            if np.isnan(weight):
                weight = 0
            
            if other_node_idx == node_idx:
                # Self-loop: currently set to 0 (not proper LFMM)
                membership_vector[other_community] += 0 * weight / 2
            else:
                membership_vector[other_community] += weight
        
        # Normalize by population
        membership_vector = membership_vector / sum(membership_vector) * st_g.vs[node_idx]['population']
        mixed_membership_vectors.append(membership_vector)
    
    return mixed_membership_vectors


def link_fraction_mixed_membership(st_g: ig.Graph, inter_attr: str,
                                    comm_attr: str = 'st_community') -> List[np.ndarray]:
    """
    Compute Link Fraction Mixed Membership (LFMM) vectors for each node.
    
    This is the primary LFMM implementation that properly handles self-loops.

    Parameters:
    -----------
    st_g : igraph.Graph
        The spatiotemporal graph
    inter_attr : str
        The name of the edge attribute containing the edge weights
    comm_attr : str
        The name of the vertex attribute containing community membership
        
    Returns:
    --------
    List[np.ndarray]
        List of LFMM vectors, one per vertex, normalized by population
    """
    communities = list(set(st_g.vs[comm_attr]))
    communities.sort()

    mixed_membership_vectors = []

    for node_idx in range(len(st_g.vs)):
        membership_vector = np.zeros(len(communities))
        
        incident_edges = st_g.incident(node_idx)
        
        for edge_idx in incident_edges:
            edge = st_g.es[edge_idx]
            other_node_idx = edge.target if edge.source == node_idx else edge.source
            other_community = st_g.vs[other_node_idx][comm_attr]
            
            weight = edge[inter_attr]

            if other_node_idx == node_idx:
                # Self-loop: count half weight
                membership_vector[other_community] += weight / 2
            else:
                membership_vector[other_community] += weight
        
        # Normalize by total and multiply by population
        membership_vector = membership_vector / sum(membership_vector) * st_g.vs[node_idx]['population']
        mixed_membership_vectors.append(membership_vector)
    
    return mixed_membership_vectors


def get_mmwf_history_by_region(st_g: ig.Graph, attr: str = 'MMWF') -> Dict[int, Dict[int, np.ndarray]]:
    """
    Get the history of Mixed Membership Weight Fraction (MMWF) vectors for each region.

    Parameters:
    -----------
    st_g : igraph.Graph
        The spatiotemporal graph with MMWF, region, and year vertex attributes
    attr : str
        The name of the vertex attribute containing the membership vectors
        (default: 'MMWF')

    Returns:
    --------
    Dict[int, Dict[int, np.ndarray]]
        A nested dictionary where:
        - Keys are region IDs
        - Values are dictionaries mapping year -> membership vector
    """
    region_history = {}
    
    for v in st_g.vs:
        region = v['region']
        year = v['year']
        mmwf = v[attr]
        
        if region not in region_history:
            region_history[region] = {}
        
        region_history[region][year] = np.array(mmwf)
        
    return region_history


def calculate_membership_diversity(membership_vector: np.ndarray) -> float:
    """
    Calculate the Gini-Simpson Index (diversity) of a membership vector.
    
    Parameters:
    -----------
    membership_vector : np.ndarray
        Vector of membership weights
        
    Returns:
    --------
    float
        Gini-Simpson Index (0 = no diversity, 1 = maximum diversity)
    """
    total = np.sum(membership_vector)
    if total <= 0:
        return np.nan
    
    proportions = membership_vector / total
    return 1 - np.sum(proportions ** 2)
