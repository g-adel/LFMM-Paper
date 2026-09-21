"""Compute the aggregability index from node aggregation and block labels."""

from collections import Counter
from collections.abc import Hashable, Sequence
from math import fsum, log


def aggregability_index(
    aggregation_labels: Sequence[Hashable],
    block_labels: Sequence[Hashable],
) -> float:
    """Return eta = I(C; P) / H(C), where C is blocks and P is aggregation.

    Both vectors describe the same original nodes in the same order. Each
    node has equal weight, and labels identify non-overlapping classes. No
    network edges or communities detected after aggregation are required.

    This calculation assumes nonempty, equally sized, one-dimensional label
    vectors containing valid hashable labels and at least two distinct blocks.
    Behavior outside these assumptions is intentionally unspecified for now.

    An index of 1 means each aggregation class belongs entirely to one block;
    an index of 0 means aggregation and block labels are independent. The
    normalization uses block entropy, so swapping the inputs can change eta.

    Reference: Gandica et al. (2020), "Measuring the effect of node aggregation
    on community detection", Section 4, Equation (2).
    https://doi.org/10.1140/epjds/s13688-020-00223-0
    """
    n_nodes = len(block_labels)
    aggregation_counts = Counter(aggregation_labels)
    block_counts = Counter(block_labels)
    joint_counts = Counter(zip(block_labels, aggregation_labels))

    block_entropy = -fsum(
        (count / n_nodes) * log(count / n_nodes)
        for count in block_counts.values()
    )
    mutual_information = fsum(
        (count / n_nodes)
        * log(
            (n_nodes * count)
            / (block_counts[block] * aggregation_counts[aggregation])
        )
        for (block, aggregation), count in joint_counts.items()
    )
    return mutual_information / block_entropy
