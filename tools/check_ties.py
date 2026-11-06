#!/usr/bin/env python3
"""Recompute every UNDECIDED case with exact fractions.

    python tools/check_ties.py
    python tools/check_ties.py fixtures/sample_data.json

Equal fractions mean a true tie, and the visible gap was floating-point error.
Different fractions mean ε hid a real difference.
"""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as npu  # noqa: E402


def exact_mac(pattern, filter_matrix):
    return sum(
        Fraction(str(a)) * Fraction(str(b))
        for row_a, row_b in zip(pattern, filter_matrix)
        for a, b in zip(row_a, row_b)
    )


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else npu.DEFAULT_DATA
    data = npu.load_dataset(path)
    filters, _, results = npu.analyze_dataset(data)
    ties = [r for r in results if r["decision"] == npu.UNDECIDED]
    print("{}: {} UNDECIDED of {} cases".format(os.path.basename(path), len(ties), len(results)))
    for result in ties:
        group = filters["size_{}".format(npu.parse_pattern_key(result["id"]))]
        pattern = data["patterns"][result["id"]]["input"]
        cross, x = exact_mac(pattern, group[npu.CROSS]), exact_mac(pattern, group[npu.X])
        print("{}: Cross {}, X {} -> {}".format(result["id"], cross, x, "true tie" if cross == x else "real difference"))


if __name__ == "__main__":
    main()
