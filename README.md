# Reproducible Analysis Package

**Comprehensive computational analysis for aggregated network communities research**

This package contains all essential code for reproducing the analyses and figures presented in the manuscript. It is a self-contained analysis framework designed for journal peer review and scientific reproducibility.

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

## Quick Start

### Run All Analyses

```bash
# Generate all figures (excludes time-intensive synthetic benchmarks)
python run_analysis.py

# Include synthetic benchmarks (may take 30+ minutes)
python run_analysis.py --include-synthetic

# Specify output directory
python run_analysis.py --output-dir ../Output/Figures
```

### Run Individual Analysis Modules

```bash
# Network analysis only
cd analysis
python network_analysis_plots.py

# Diversity analysis only
python diversity_analysis_plots.py

# Mixed membership analysis only
python mixed_membership_plots.py

# Synthetic benchmarks only
python synthetic_benchmarks.py
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

**Key Functions:**
- `link_fraction_mixed_membership()` - Core LFMM implementation
- `mixed_membership_link_weight()` - Alternative membership calculation
- `get_mmwf_history_by_region()` - Extract temporal membership histories
- `calculate_membership_diversity()` - Gini-Simpson Index calculation

### 2. Graph Aggregation (`core/graph_aggregation.py`)

Functions for aggregating spatiotemporal networks:

```python
from core import graph_aggregation

# Aggregate by community and year
comm_graph = graph_aggregation.aggregate_graph_by_community_year(st_graph)

# Aggregate by municipality (gemeente) and year
gm_graph = graph_aggregation.aggregate_graph_by_gemeente_year(st_graph)
```

**Key Functions:**
- `aggregate_graph_by_community_year()` - Community-level aggregation
- `aggregate_graph_by_gemeente_year()` - Municipality-level aggregation

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

**Key Functions:**
- `extract_yearly_graphs_no_type()` - Extract yearly graph slices
- `extract_interlayer_graphs()` - Extract temporal transitions
- `get_contingency_matrix()` - Create transition matrices

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

**Key Functions:**
- `plot_graph_with_style()` - Main plotting function
- `get_vertex_colors()` - Community-based coloring

## Generated Figures

### Network Analysis
- `Community-Aggregated_Network_2021.png` - Community-level density matrix
- `RGB_Composite_Connection_Types_2021.png` - Connection type composition

### Mixed Membership
- `GM_CD_network_2021.png` - Municipality network (community detection)
- `GM_MM_2021.png` - Municipality network (mixed membership)
- `mixed_membership_WK_GM_comparison.png` - Multi-scale comparison

### Diversity Analysis
- `Evolution_of_Gini-Simpson_index_over_time.png` - Temporal diversity
- `Div_vs_Urban_Density.png` - Urban density correlation
- `Membership_Composition_in_Northern_Regions.png` - Composition dynamics

### Synthetic Benchmarks
- `LFMM_synthetic_heatmap.png` - Parameter space exploration

## Data Requirements

The package expects the following data files:

1. **Main Graph** (required):
   ```
   Mixed_membership/transverse_graph_wijk_CD_MM_cleaned.pkl
   ```
   Spatiotemporal network with:
   - Vertex attributes: `year`, `region`, `st_community`, `population`, `members`, `LFMM`
   - Edge attributes: `multi_count`, `family_count`, `colleague_count`, `school_count`, `mobility`

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

### Installation

```bash
# Using pip
pip install igraph numpy pandas scipy matplotlib

# Using conda
conda install -c conda-forge python-igraph numpy pandas scipy matplotlib cairo
```

## Algorithm Details

### Link Fraction Mixed Membership (LFMM)

The LFMM algorithm computes soft community membership based on edge distributions:

For each node $i$, the membership vector $\mathbf{m}_i$ is calculated as:

$$m_i(c) = \frac{\sum_{j \in \mathcal{N}(i), \delta(j)=c} w_{ij}}{\sum_{j \in \mathcal{N}(i)} w_{ij}} \cdot p_i$$

where:
- $\mathcal{N}(i)$ is the neighborhood of node $i$
- $\delta(j)$ is the community assignment of node $j$
- $w_{ij}$ is the edge weight between nodes $i$ and $j$
- $p_i$ is the population of node $i$

### Gini-Simpson Index

Diversity is measured using the Gini-Simpson Index:

$$GSI = 1 - \sum_{c=1}^{k} \left(\frac{m_i(c)}{\sum_{c'} m_i(c')}\right)^2$$

where $k$ is the number of communities.

## Configuration

### Community Names

Modify in `utils.py`:

```python
COMM_NAMES = [
    'Northern',
    'Overijsel-aligned',
    'North Holland-aligned',
    # ... etc
]
```

### Color Palette

Modify in `utils.py`:

```python
COMMUNITY_PALETTE = [colorsys.hls_to_rgb(h, 0.45, 1) 
                     for h in [0, .1, .17, .25, .5, .58, .7, .78, .88]]
```

## Extending the Package

### Adding New Analyses

1. Create a new module in `analysis/`:
   ```python
   # analysis/my_new_analysis.py
   from utils import load_transverse_graph
   
   def generate_my_figure(year=2021, output_dir='Assets'):
       g = load_transverse_graph()
       # Your analysis here
       # ...
   ```

2. Add to `run_analysis.py`:
   ```python
   import my_new_analysis
   
   # In generate_all_figures():
   my_new_analysis.generate_my_figure(year=2021, output_dir=output_dir)
   ```

### Adding New Core Functions

Add to appropriate module in `core/`:

```python
# core/mixed_membership.py

def my_new_metric(graph, attribute):
    """Calculate custom metric."""
    # Implementation
    pass
```

## Troubleshooting

### Import Errors

Ensure you're running from the correct directory:
```bash
cd /path/to/Communities_in_aggregated_networks
python reproducible_analysis/run_analysis.py
```

### Missing Graph Data

The package will search multiple locations for data files. If not found, you'll see:
```
FileNotFoundError: Could not find transverse_graph_wijk_CD_MM_cleaned.pkl
```

Place the data file in one of:
- `Mixed_membership/transverse_graph_wijk_CD_MM_cleaned.pkl`
- `Data/transverse_graph_wijk_CD_MM_cleaned.pkl`
- `reproducible_analysis/data/transverse_graph_wijk_CD_MM_cleaned.pkl`

### Memory Issues

For large graphs or synthetic benchmarks:
- Close other applications
- Reduce grid resolution in synthetic benchmarks
- Process years individually rather than all at once

### Cairo/Plotting Issues

If network visualization fails:
```bash
# Install Cairo library
conda install -c conda-forge cairo

# Or on Ubuntu/Debian
sudo apt-get install libcairo2-dev
```

## Citation

If you use this code in your research, please cite:

```bibtex
@article{yourpaper2026,
  title={Communities in Aggregated Networks},
  author={Your Name},
  journal={Journal Name},
  year={2026}
}
```

## License

This code is provided for peer review and scientific reproducibility.

## Contact

For questions or issues with the reproducible analysis package, please contact:
[Your contact information]

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Compatibility**: Python 3.8+
