"""
Main script to run all reproducible analyses and generate manuscript figures.
Coordinates the execution of all analysis modules.
"""

import os
import sys
import argparse
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'analysis'))

# Import analysis modules
import network_analysis_plots
import diversity_analysis_plots
import mixed_membership_plots
import synthetic_benchmarks


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def generate_all_figures(output_dir: str = 'Assets', 
                        skip_synthetic: bool = False):
    """
    Generate all manuscript figures.
    
    Args:
        output_dir: Output directory for figures
        skip_synthetic: Skip time-intensive synthetic benchmarks
    """
    start_time = datetime.now()
    print_header("REPRODUCIBLE NETWORK ANALYSIS - MANUSCRIPT FIGURES")
    print(f"Output directory: {output_dir}")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Network Analysis Plots
    print_header("1. NETWORK ANALYSIS")
    try:
        network_analysis_plots.generate_community_aggregated_network(
            year=2021, output_dir=output_dir)
        network_analysis_plots.generate_rgb_composite_connection_types(
            year=2021, output_dir=output_dir)
    except Exception as e:
        print(f"⚠ Error in network analysis: {e}")
    
    # 2. Mixed Membership Analysis
    print_header("2. MIXED MEMBERSHIP ANALYSIS")
    try:
        mixed_membership_plots.generate_gemeente_network_visualization(
            year=2021, method='CD', output_dir=output_dir)
        mixed_membership_plots.generate_gemeente_network_visualization(
            year=2021, method='MM', output_dir=output_dir)
        mixed_membership_plots.generate_mixed_membership_comparison(
            year=2021, output_dir=output_dir)
    except Exception as e:
        print(f"⚠ Error in mixed membership analysis: {e}")
    
    # 3. Diversity Analysis
    print_header("3. DIVERSITY ANALYSIS")
    try:
        diversity_analysis_plots.generate_gsi_evolution_plot(
            year_from=2009, year_to=2022, output_dir=output_dir)
        diversity_analysis_plots.generate_diversity_vs_urban_density(
            year=2021, output_dir=output_dir)
        diversity_analysis_plots.generate_membership_composition(
            target_communities=[0, 4], year_from=2009, year_to=2022,
            output_dir=output_dir)
    except Exception as e:
        print(f"⚠ Error in diversity analysis: {e}")
    
    # 4. Synthetic Benchmarks
    if not skip_synthetic:
        print_header("4. SYNTHETIC BENCHMARKS")
        try:
            synthetic_benchmarks.generate_lfmm_synthetic_heatmap(
                output_dir=output_dir)
        except Exception as e:
            print(f"⚠ Error in synthetic benchmarks: {e}")
    else:
        print_header("4. SYNTHETIC BENCHMARKS (SKIPPED)")
        print("Skipping time-intensive synthetic benchmarks.")
        print("Run with --include-synthetic to generate these figures.\n")
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("GENERATION COMPLETE")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time: {duration}")
    print(f"\nAll figures saved to: {output_dir}/\n")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate all manuscript figures for the aggregated networks study."
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='Assets',
        help='Output directory for generated figures (default: Assets)'
    )
    parser.add_argument(
        '--include-synthetic',
        action='store_true',
        help='Include time-intensive synthetic benchmark figures'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2021,
        help='Year for single-year figures (default: 2021)'
    )
    
    args = parser.parse_args()
    
    # Generate figures
    generate_all_figures(
        output_dir=args.output_dir,
        skip_synthetic=not args.include_synthetic
    )


if __name__ == "__main__":
    main()
