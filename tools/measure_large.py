#!/usr/bin/env python3
"""Measure one large case stage by stage, using main.py's real functions.

    python tools/measure_large.py          # 1000×1000
    python tools/measure_large.py 500

The assignment's sizes stop at 25×25; this shows what limits a much larger case.
"""

import json
import math
import operator
import os
import platform
import random
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main as npu  # noqa: E402

REPEATS = 3


def matrix(n, seed):
    rng = random.Random(seed)
    return [[round(rng.random(), 1) for _ in range(n)] for _ in range(n)]


def timed(func, *args):
    return npu.measure_ms(func, *args, repeats=REPEATS)


def peak_mib(func, *args):
    tracemalloc.start()
    kept = func(*args)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    del kept
    return peak / 1048576


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    pattern, cross, x = matrix(n, 1), matrix(n, 2), matrix(n, 3)
    text = json.dumps({"filters": {"cross": cross, "x": x}, "pattern": pattern})
    flat_p, flat_f = npu.flatten(pattern), npu.flatten(cross)

    print("Python {} · {} · {}×{} · mean of {} runs".format(platform.python_version(), platform.machine(), n, n, REPEATS))
    print("JSON text: {:.1f} MiB (3 matrices)".format(len(text) / 1048576))
    print("JSON parse peak memory: {:.1f} MiB".format(peak_mib(json.loads, text)))
    print()
    rows = [
        ("json.loads, 3 matrices", timed(json.loads, text)),
        ("validate_matrix × 3", 3 * timed(npu.validate_matrix, pattern, n)),
        ("mac × 2", 2 * timed(npu.mac, pattern, cross)),
        ("decide", timed(npu.decide, 1.0, 2.0)),
    ]
    total = sum(ms for _, ms in rows)
    for name, ms in rows:
        print("{:<26}{:>12.3f} ms {:>6.1f} %".format(name, ms, ms / total * 100))
    print("{:<26}{:>12.3f} ms".format("one case", total))
    print()
    print("One MAC pass, {} multiplications:".format(n * n))
    print("{:<26}{:>12.3f} ms".format("mac (2D loop)", timed(npu.mac, pattern, cross)))
    print("{:<26}{:>12.3f} ms".format("mac_flat (1D loop)", timed(npu.mac_flat, flat_p, flat_f)))
    print("{:<26}{:>12.3f} ms".format("sum(map(mul))", timed(lambda: sum(map(operator.mul, flat_p, flat_f)))))
    if hasattr(math, "sumprod"):
        print("{:<26}{:>12.3f} ms".format("math.sumprod (3.12+)", timed(math.sumprod, flat_p, flat_f)))

    # A Cross filter is mostly zeros, so only its non-zero cells need multiplying.
    sparse_filter = npu.make_cross(n)
    cells = [(i, j, v) for i, row in enumerate(sparse_filter) for j, v in enumerate(row) if v]
    print()
    print("Generated Cross filter, {} non-zero cells of {}:".format(len(cells), n * n))
    print("{:<26}{:>12.3f} ms".format("mac (all cells)", timed(npu.mac, pattern, sparse_filter)))
    print("{:<26}{:>12.3f} ms".format("non-zero cells only", timed(lambda: sum(pattern[i][j] * v for i, j, v in cells))))

    # The same products in reverse order have the same exact sum, so any gap is rounding error.
    forward = npu.mac(pattern, cross)
    backward = npu.mac([row[::-1] for row in pattern[::-1]], [row[::-1] for row in cross[::-1]])
    print()
    print("Same products, reversed order:")
    print("gap {:.3g}, score {:.6f}, decide: {}".format(abs(forward - backward), forward, npu.decide(forward, backward)))
    print("math.fsum gap: {:.3g}".format(abs(math.fsum(a * b for a, b in zip(flat_p, flat_f)) - math.fsum(a * b for a, b in zip(reversed(flat_p), reversed(flat_f))))))


if __name__ == "__main__":
    main()
