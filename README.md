# Reproducible Analysis Package

**Comprehensive computational analysis for aggregated network communities research**

This package contains all essential code for reproducing the analyses and figures presented in the paper *Link Fraction Mixed Membership Reveals Community Diversity in Aggregated Social Networks*.

## Package Structure

```
reproducible_analysis/
├── core/                          # Core analysis algorithms
│   ├── mixed_membership.py        # LFMM implementation
│   ├── graph_aggregation.py       # Network aggregation functions  
│   └── temporal_analysis.py       # Temporal network analysis
│
├── visualization/                 # Visualization functions
│   └── network_visualization.py   # Network plotting utilities
│
├── analysis/                      # Analysis scripts for figures
│   ├── network_analysis_plots.py      # Network visualizations
│   ├── mixed_membership_plots.py      # Mixed membership analyses
│   ├── diversity_analysis_plots.py    # Diversity analyses
│   └── synthetic_benchmarks.py        # Synthetic validation
│
├── utils.py                       # Common utilities and data loading
├── run_analysis.py                # Main script to run all analyses
└── README.md                      # This file
```

## Core Modules

### 1. Mixed Membership (`core/mixed_membership.py`)

Implements the **Link Fraction Mixed Membership (LFMM)** algorithm:

```python
from core import mixed_membership

# Calculate LFMM vectors for all nodes
lfmm_vectors = mixed_membership.link_fraction_mixed_membership(
    graph, 
    inter_attr='multi_count',
    comm_attr='st_community'
)

# Calculate diversity (Gini-Simpson Index)
diversity = mixed_membership.calculate_membership_diversity(membership_vector)
```

### 2. Graph Aggregation (`core/graph_aggregation.py`)

Functions for aggregating spatiotemporal networks:

```python
from core import graph_aggregation

# Aggregate by community and year
comm_graph = graph_aggregation.aggregate_graph_by_community_year(st_graph)

# Aggregate by municipality (gemeente) and year
gm_graph = graph_aggregation.aggregate_graph_by_gemeente_year(st_graph)
```

### 3. Temporal Analysis (`core/temporal_analysis.py`)

Temporal network slicing and transition analysis:

```python
from core import temporal_analysis

# Extract yearly snapshots
yearly_graphs = temporal_analysis.extract_yearly_graphs_no_type(st_graph)

# Extract interlayer transitions
transitions = temporal_analysis.extract_interlayer_graphs(st_graph)

# Get contingency matrix
cont_matrix = temporal_analysis.get_contingency_matrix(bipartite_graph)
```

### 4. Network Visualization (`visualization/network_visualization.py`)

Community-aware network plotting:

```python
from visualization import network_visualization

# Plot network with community coloring
network_visualization.plot_graph_with_style(
    graph,
    membership_attribute='st_community',
    palette=community_colors,
    legend=True,
    target='output.png'
)
```


## Data Requirements

The package expects the following data files:

1. **Main Graph** (required):
   ```
   Mixed_membership/transverse_graph_wijk_CD_MM_cleaned.pkl
   ```
   Spatiotemporal network with:
   - Vertex attributes: `year`, `region`, `st_community`, `population`
   - Edge attributes: `multi_count`, `mobility`

2. **Urbanness Data** (for diversity analysis):
   ```
   Data/cleanup/wijk_urbanness_2021.csv
   Data/cleanup/gemeente_urbanness_2021.csv
   ```

## Dependencies

### Required Libraries

```python
# Core scientific computing
numpy>=1.21
pandas>=1.3
scipy>=1.7

# Network analysis
igraph>=0.10.0
networkx>=2.8

# Visualization
matplotlib>=3.5
cairo  # For network rendering

# Optional but recommended
leidenalg  # For community detection
ternary    # For ternary plots
geopandas  # For spatial visualization
```

