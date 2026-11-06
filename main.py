#!/usr/bin/env python3
"""Mini NPU Simulator — classify N×N patterns with a hand-written MAC loop.

Standard library only. Python 3.8+.

    python main.py                 # choose a mode interactively
    python main.py --mode 2        # analyse data.json directly
    python main.py --lang en       # English console output
"""

import argparse
import json
import math
import os
import re
import sys
import time

EPSILON = 1e-9
BENCH_SIZES = (3, 5, 13, 25)
BENCH_REPEATS = 10

CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"

# Failure categories named by the assignment's report section.
CAT_SCHEMA = "DATA / SCHEMA"
CAT_SIZE = "MATRIX SIZE"
CAT_LABEL = "LABEL NORMALIZATION"
CAT_NUMERIC = "NUMERICAL COMPARISON"
CAT_LOGIC = "CLASSIFICATION LOGIC"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(BASE_DIR, "data.json")
SAMPLE_DATA = os.path.join(BASE_DIR, "fixtures", "sample_data.json")

LABEL_ALIASES = {"+": CROSS, "cross": CROSS, "x": X}

MESSAGES = {
    "ko": {
        "title": "=== Mini NPU Simulator ===",
        "menu": "[모드 선택]\n1. 사용자 입력 (3x3)\n2. data.json 분석",
        "choose": "선택: ",
        "menu_error": "1 또는 2를 입력하세요.",
        "bye": "입력이 종료되어 프로그램을 마칩니다.",
        "sec_filter_input": "[1] 필터 입력",
        "sec_pattern_input": "[2] 패턴 입력",
        "sec_mac": "[3] MAC 결과",
        "sec_perf_3": "[4] 성능 분석 (3×3, 평균/{repeats}회)",
        "sec_filter_load": "[1] 필터 로드",
        "sec_patterns": "[2] 패턴 분석 (라벨 정규화 적용)",
        "sec_perf": "[3] 성능 분석 (평균/{repeats}회)",
        "sec_flat": "[3-보너스] 2차원 vs 1차원 접근 (평균/{repeats}회, 동일 입력)",
        "sec_summary": "[4] 결과 요약",
        "matrix_prompt": "{name} ({n}줄 입력, 공백 구분 — 'cross' 또는 'x'를 입력하면 자동 생성)",
        "filter_a": "필터 A",
        "filter_b": "필터 B",
        "pattern": "패턴",
        "generated": "  → {label} 패턴을 자동 생성했습니다.",
        "saved": "✓ {name} 저장 완료:",
        "err_columns": "입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요. (받은 개수: {got})",
        "err_number": "입력 형식 오류: 숫자로 변환할 수 없는 값입니다: {value!r}",
        "err_finite": "입력 형식 오류: 유한한 숫자만 입력할 수 있습니다: {value!r}",
        "err_rows": "입력 형식 오류: {n}개 행이 필요하지만 {got}개 행만 입력되었습니다. 이 행렬을 처음부터 다시 입력하세요.",
        "score_a": "A 점수: {score}",
        "score_b": "B 점수: {score}",
        "time_avg": "연산 시간(평균/{repeats}회): {ms:.6f} ms",
        "verdict": "판정: {verdict}",
        "verdict_tie": "판정 불가 (|A-B| < {epsilon:g})",
        "using_sample": "! data.json이 없어 데모용 fixture를 사용합니다 (공식 과제 데이터가 아닙니다): {path}",
        "dataset_path": "데이터 파일: {path}",
        "filter_ok": "✓ {group} 필터 로드 완료 (Cross, X)",
        "filter_bad": "✗ {group} 필터 로드 실패: {reason}",
        "dataset_failed": "데이터 파일을 분석할 수 없습니다 [{category}]: {reason}",
        "cross_score": "Cross 점수: {score}",
        "x_score": "X 점수: {score}",
        "case_line": "판정: {decision} | expected: {expected} | {status}",
        "case_failed": "FAIL [{category}] {reason}",
        "table_head": "크기        평균 시간(ms)      연산 횟수",
        "flat_head": "크기        2차원(ms)      1차원(ms)      1차원/2차원",
        "total": "총 테스트: {n}개",
        "passed": "통과: {n}개",
        "failed": "실패: {n}개",
        "failures": "실패 케이스:",
        "no_failures": "실패 케이스 없음",
        "detail_hint": '(상세 원인 분석과 복잡도 설명은 README.md의 "결과 리포트" 섹션 참고)',
        "r_file_missing": "파일을 찾을 수 없습니다: {path}",
        "r_file_unreadable": "파일을 읽을 수 없습니다: {detail}",
        "r_json_syntax": "JSON 문법 오류 (줄 {line}, 열 {col}): {detail}",
        "r_top_not_object": "최상위 값은 객체여야 합니다.",
        "r_top_missing": "최상위 필드 '{field}'이(가) 없습니다.",
        "r_field_not_object": "'{field}' 값은 객체여야 합니다.",
        "r_group_key": "필터 그룹 키는 size_N 형식이어야 합니다: {key!r}",
        "r_group_missing": "필터 그룹 {group}을(를) 찾을 수 없습니다.",
        "r_group_broken": "필터 그룹 {group}을(를) 사용할 수 없습니다: {reason}",
        "r_group_not_object": "필터 그룹은 객체여야 합니다.",
        "r_group_labels": "Cross와 X 필터가 정확히 하나씩 있어야 합니다 (발견: {found}).",
        "r_group_duplicate": "정규화 후 같은 라벨이 중복됩니다: {label}",
        "r_case_key": "패턴 키는 size_N_idx 형식이어야 합니다: {key!r}",
        "r_case_not_object": "패턴 항목은 객체여야 합니다.",
        "r_case_field": "패턴 필드 '{field}'이(가) 없습니다.",
        "r_label": "지원하지 않는 라벨입니다: {value!r}",
        "r_not_matrix": "2차원 배열이 아닙니다.",
        "r_rows": "행 수 불일치: {expected}행이 필요하지만 {got}행입니다.",
        "r_columns": "열 수 불일치: {row}번째 행은 {expected}열이어야 하지만 {got}열입니다.",
        "r_cell": "숫자가 아닌 값입니다 ({row}, {col}): {value!r}",
        "r_nonfinite_score": "점수가 유한한 숫자가 아닙니다 (Cross={a}, X={b}).",
        "r_tie": "동점(UNDECIDED) 처리 규칙에 따라 FAIL: |Cross−X| = {diff:.3g} < {epsilon:g}",
        "r_mismatch": "판정({decision})이 expected({expected})와 다릅니다.",
    },
    "en": {
        "title": "=== Mini NPU Simulator ===",
        "menu": "[Select mode]\n1. Manual input (3x3)\n2. Analyse data.json",
        "choose": "Choice: ",
        "menu_error": "Please enter 1 or 2.",
        "bye": "Input closed. Exiting.",
        "sec_filter_input": "[1] Filter input",
        "sec_pattern_input": "[2] Pattern input",
        "sec_mac": "[3] MAC result",
        "sec_perf_3": "[4] Performance (3×3, mean of {repeats} runs)",
        "sec_filter_load": "[1] Load filters",
        "sec_patterns": "[2] Analyse patterns (labels normalized)",
        "sec_perf": "[3] Performance (mean of {repeats} runs)",
        "sec_flat": "[3-bonus] 2D vs 1D access (mean of {repeats} runs, same input)",
        "sec_summary": "[4] Summary",
        "matrix_prompt": "{name} ({n} lines, space separated — type 'cross' or 'x' to generate one)",
        "filter_a": "Filter A",
        "filter_b": "Filter B",
        "pattern": "Pattern",
        "generated": "  → Generated a {label} pattern.",
        "saved": "✓ {name} saved:",
        "err_columns": "Input format error: enter {n} space-separated numbers per line. (got {got})",
        "err_number": "Input format error: not a number: {value!r}",
        "err_finite": "Input format error: only finite numbers are allowed: {value!r}",
        "err_rows": "Input format error: {n} rows are required but only {got} were entered. Re-enter this matrix from the start.",
        "score_a": "Score A: {score}",
        "score_b": "Score B: {score}",
        "time_avg": "Compute time (mean of {repeats} runs): {ms:.6f} ms",
        "verdict": "Decision: {verdict}",
        "verdict_tie": "UNDECIDED (|A-B| < {epsilon:g})",
        "using_sample": "! data.json not found; using the demo fixture (NOT the official assignment data): {path}",
        "dataset_path": "Data file: {path}",
        "filter_ok": "✓ {group} filters loaded (Cross, X)",
        "filter_bad": "✗ {group} filters failed: {reason}",
        "dataset_failed": "Cannot analyse the data file [{category}]: {reason}",
        "cross_score": "Cross score: {score}",
        "x_score": "X score: {score}",
        "case_line": "Decision: {decision} | expected: {expected} | {status}",
        "case_failed": "FAIL [{category}] {reason}",
        "table_head": "Size        Mean time (ms)     MAC count",
        "flat_head": "Size        2D (ms)        1D (ms)        1D/2D",
        "total": "Total tests: {n}",
        "passed": "Passed: {n}",
        "failed": "Failed: {n}",
        "failures": "Failed cases:",
        "no_failures": "No failed cases",
        "detail_hint": '(See the "Result Report" section of README.en.md for the analysis)',
        "r_file_missing": "File not found: {path}",
        "r_file_unreadable": "Cannot read file: {detail}",
        "r_json_syntax": "JSON syntax error (line {line}, column {col}): {detail}",
        "r_top_not_object": "The top-level value must be an object.",
        "r_top_missing": "Missing top-level field '{field}'.",
        "r_field_not_object": "'{field}' must be an object.",
        "r_group_key": "Filter group keys must look like size_N: {key!r}",
        "r_group_missing": "Filter group {group} does not exist.",
        "r_group_broken": "Filter group {group} is unusable: {reason}",
        "r_group_not_object": "A filter group must be an object.",
        "r_group_labels": "Exactly one Cross and one X filter are required (found: {found}).",
        "r_group_duplicate": "Labels collide after normalization: {label}",
        "r_case_key": "Pattern keys must look like size_N_idx: {key!r}",
        "r_case_not_object": "A pattern entry must be an object.",
        "r_case_field": "Missing pattern field '{field}'.",
        "r_label": "Unsupported label: {value!r}",
        "r_not_matrix": "Not a two-dimensional array.",
        "r_rows": "Row count mismatch: expected {expected}, got {got}.",
        "r_columns": "Column count mismatch: row {row} needs {expected} columns, got {got}.",
        "r_cell": "Non-numeric value at ({row}, {col}): {value!r}",
        "r_nonfinite_score": "Score is not a finite number (Cross={a}, X={b}).",
        "r_tie": "FAIL under the tie rule (UNDECIDED): |Cross−X| = {diff:.3g} < {epsilon:g}",
        "r_mismatch": "Decision {decision} does not match expected {expected}.",
    },
}


class Reason:
    """A translatable failure message: a message key plus its parameters."""

    def __init__(self, message, **params):
        self.key = message
        self.params = params

    def render(self, lang="ko"):
        params = {
            k: (v.render(lang) if isinstance(v, Reason) else v)
            for k, v in self.params.items()
        }
        return MESSAGES[lang][self.key].format(**params)


class NpuError(Exception):
    """A validation failure carrying its report category and reason."""

    def __init__(self, category, message, **params):
        super().__init__(message)
        self.category = category
        self.reason = Reason(message, **params)


# ---------------------------------------------------------------------------
# MAC
# ---------------------------------------------------------------------------

def mac(pattern, filter_matrix):
    """Multiply-accumulate two same-sized square matrices with a double loop."""
    n = len(pattern)
    score = 0.0
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
    return score


def flatten(matrix):
    """Bonus: turn an N×N matrix into a flat list of length N²."""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(flat_pattern, flat_filter):
    """Bonus: the same MAC over flat lists, walking a single index."""
    score = 0.0
    for k in range(len(flat_pattern)):
        score += flat_pattern[k] * flat_filter[k]
    return score


# ---------------------------------------------------------------------------
# Pattern generator (bonus)
# ---------------------------------------------------------------------------

def make_cross(n):
    """Build an N×N Cross: the middle row and column are 1."""
    low, high = (n - 1) // 2, n // 2
    return [
        [1.0 if i in (low, high) or j in (low, high) else 0.0 for j in range(n)]
        for i in range(n)
    ]


def make_x(n):
    """Build an N×N X: both diagonals are 1."""
    return [
        [1.0 if i == j or i + j == n - 1 else 0.0 for j in range(n)]
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Labels and decisions
# ---------------------------------------------------------------------------

def normalize_label(value):
    """Map any accepted spelling to the canonical Cross or X label."""
    if isinstance(value, str):
        canonical = LABEL_ALIASES.get(value.strip().lower())
        if canonical is not None:
            return canonical
    raise NpuError(CAT_LABEL, "r_label", value=value)


def decide(score_a, score_b, label_a="A", label_b="B", epsilon=EPSILON):
    """Pick the higher score, or UNDECIDED when they are within epsilon."""
    if abs(score_a - score_b) < epsilon:
        return UNDECIDED
    return label_a if score_a > score_b else label_b


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def to_finite_float(value):
    """Convert a JSON cell to float; bools, NaN and infinities are rejected."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(value)
    try:
        number = float(value)
    except OverflowError:
        raise ValueError(value)
    if not math.isfinite(number):
        raise ValueError(value)
    return number


def validate_matrix(matrix, size):
    """Return a float copy of a size×size matrix, or raise NpuError."""
    if not isinstance(matrix, list):
        raise NpuError(CAT_SCHEMA, "r_not_matrix")
    if len(matrix) != size:
        raise NpuError(CAT_SIZE, "r_rows", expected=size, got=len(matrix))
    result = []
    for i, row in enumerate(matrix):
        if not isinstance(row, list):
            raise NpuError(CAT_SCHEMA, "r_not_matrix")
        if len(row) != size:
            raise NpuError(CAT_SIZE, "r_columns", row=i + 1, expected=size, got=len(row))
        cells = []
        for j, value in enumerate(row):
            try:
                cells.append(to_finite_float(value))
            except ValueError:
                raise NpuError(CAT_SCHEMA, "r_cell", row=i + 1, col=j + 1, value=value)
        result.append(cells)
    return result


def parse_row(line, n):
    """Parse one console line into n numbers, or raise NpuError."""
    tokens = line.split()
    if len(tokens) != n:
        raise NpuError(CAT_SIZE, "err_columns", n=n, got=len(tokens))
    row = []
    for token in tokens:
        try:
            number = float(token)
        except ValueError:
            raise NpuError(CAT_SCHEMA, "err_number", value=token)
        if not math.isfinite(number):
            raise NpuError(CAT_SCHEMA, "err_finite", value=token)
        row.append(number)
    return row


# ---------------------------------------------------------------------------
# data.json
# ---------------------------------------------------------------------------

def load_dataset(path):
    """Read and shape-check the top level of a dataset, or raise NpuError."""
    try:
        with open(path, encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise NpuError(CAT_SCHEMA, "r_file_missing", path=path)
    except json.JSONDecodeError as error:
        raise NpuError(CAT_SCHEMA, "r_json_syntax", line=error.lineno, col=error.colno, detail=error.msg)
    except (OSError, UnicodeDecodeError, RecursionError) as error:
        raise NpuError(CAT_SCHEMA, "r_file_unreadable", detail=str(error))
    if not isinstance(data, dict):
        raise NpuError(CAT_SCHEMA, "r_top_not_object")
    for field in ("filters", "patterns"):
        if field not in data:
            raise NpuError(CAT_SCHEMA, "r_top_missing", field=field)
        if not isinstance(data[field], dict):
            raise NpuError(CAT_SCHEMA, "r_field_not_object", field=field)
    return data


def parse_group_size(key):
    match = re.fullmatch(r"size_(\d+)", key)
    if not match or int(match.group(1)) == 0:
        raise NpuError(CAT_SCHEMA, "r_group_key", key=key)
    return int(match.group(1))


def load_filter_group(key, group):
    """Validate one size_N group into {Cross: matrix, X: matrix}."""
    size = parse_group_size(key)
    if not isinstance(group, dict):
        raise NpuError(CAT_SCHEMA, "r_group_not_object")
    filters = {}
    for raw_label, matrix in group.items():
        label = normalize_label(raw_label)
        if label in filters:
            raise NpuError(CAT_LABEL, "r_group_duplicate", label=label)
        filters[label] = validate_matrix(matrix, size)
    if set(filters) != {CROSS, X}:
        raise NpuError(CAT_SCHEMA, "r_group_labels", found=sorted(filters))
    return filters


def load_filters(raw_filters):
    """Validate every filter group; a broken group never stops the others."""
    filters, errors = {}, {}
    for key, group in raw_filters.items():
        try:
            filters[key] = load_filter_group(key, group)
        except NpuError as error:
            errors[key] = error
    return filters, errors


def parse_pattern_key(key):
    """Extract N from a size_N_idx pattern key."""
    match = re.fullmatch(r"size_(\d+)_(.+)", key)
    if not match or int(match.group(1)) == 0:
        raise NpuError(CAT_SCHEMA, "r_case_key", key=key)
    return int(match.group(1))


def evaluate_case(key, case, filters, filter_errors):
    """Score one pattern against its filters; raises NpuError on bad data."""
    size = parse_pattern_key(key)
    if not isinstance(case, dict):
        raise NpuError(CAT_SCHEMA, "r_case_not_object")
    for field in ("input", "expected"):
        if field not in case:
            raise NpuError(CAT_SCHEMA, "r_case_field", field=field)
    expected = normalize_label(case["expected"])

    group_key = "size_{}".format(size)
    if group_key in filter_errors:
        broken = filter_errors[group_key]
        raise NpuError(broken.category, "r_group_broken", group=group_key, reason=broken.reason)
    if group_key not in filters:
        raise NpuError(CAT_SCHEMA, "r_group_missing", group=group_key)

    pattern = validate_matrix(case["input"], size)
    score_cross = mac(pattern, filters[group_key][CROSS])
    score_x = mac(pattern, filters[group_key][X])
    return expected, score_cross, score_x


def analyze_case(key, case, filters, filter_errors=None):
    """Return the result record for one case. Bad data becomes a FAIL record."""
    result = {
        "id": key,
        "score_cross": None,
        "score_x": None,
        "decision": None,
        "expected": None,
        "passed": False,
        "category": None,
        "reason": None,
    }
    try:
        expected, score_cross, score_x = evaluate_case(key, case, filters, filter_errors or {})
    except NpuError as error:
        result["category"] = error.category
        result["reason"] = error.reason
        return result

    result.update(expected=expected, score_cross=score_cross, score_x=score_x)
    if not (math.isfinite(score_cross) and math.isfinite(score_x)):
        result["category"] = CAT_NUMERIC
        result["reason"] = Reason("r_nonfinite_score", a=score_cross, b=score_x)
        return result

    decision = decide(score_cross, score_x, CROSS, X)
    result["decision"] = decision
    if decision == expected:
        result["passed"] = True
    elif decision == UNDECIDED:
        result["category"] = CAT_NUMERIC
        result["reason"] = Reason("r_tie", diff=abs(score_cross - score_x), epsilon=EPSILON)
    else:
        result["category"] = CAT_LOGIC
        result["reason"] = Reason("r_mismatch", decision=decision, expected=expected)
    return result


def analyze_dataset(data):
    """Run every pattern of a loaded dataset through analyze_case."""
    filters, filter_errors = load_filters(data["filters"])
    results = [
        analyze_case(key, case, filters, filter_errors)
        for key, case in data["patterns"].items()
    ]
    return filters, filter_errors, results


def summarize(results):
    passed = sum(1 for r in results if r["passed"])
    return {"total": len(results), "passed": passed, "failed": len(results) - passed}


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def measure_ms(func, *args, repeats=BENCH_REPEATS):
    """Mean wall time of func(*args) in ms. Only the call itself is timed."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    total_ns = 0
    for _ in range(repeats):
        start = time.perf_counter_ns()
        func(*args)
        total_ns += time.perf_counter_ns() - start
    return total_ns / repeats / 1e6


def benchmark(sizes=BENCH_SIZES, repeats=BENCH_REPEATS):
    """Measure the MAC loop per size on generated Cross data."""
    rows = []
    for n in sizes:
        pattern, filter_matrix = make_cross(n), make_cross(n)
        rows.append({
            "n": n,
            "mac_count": n * n,
            "avg_ms": measure_ms(mac, pattern, filter_matrix, repeats=repeats),
        })
    return rows


def benchmark_flat(sizes=BENCH_SIZES, repeats=BENCH_REPEATS):
    """Bonus: compare the 2D loop against the 1D loop on identical input."""
    rows = []
    for n in sizes:
        pattern, filter_matrix = make_cross(n), make_cross(n)
        flat_pattern, flat_filter = flatten(pattern), flatten(filter_matrix)
        rows.append({
            "n": n,
            "avg_ms_2d": measure_ms(mac, pattern, filter_matrix, repeats=repeats),
            "avg_ms_1d": measure_ms(mac_flat, flat_pattern, flat_filter, repeats=repeats),
        })
    return rows


# ---------------------------------------------------------------------------
# Console
# ---------------------------------------------------------------------------

class Console:
    def __init__(self, lang="ko"):
        self.lang = lang

    def t(self, key, **params):
        return MESSAGES[self.lang][key].format(**params)

    def say(self, key, **params):
        print(self.t(key, **params))

    def section(self, key, **params):
        print()
        print("#" + "-" * 39)
        print("# " + self.t(key, **params))
        print("#" + "-" * 39)

    def matrix(self, matrix):
        for row in matrix:
            print("  " + " ".join("{:g}".format(v) for v in row))

    def perf_table(self, rows):
        self.say("table_head")
        print("-" * 41)
        for row in rows:
            size = "{0}×{0}".format(row["n"])
            print("{:<10}{:>14.6f}{:>15}".format(size, row["avg_ms"], row["mac_count"]))

    def flat_table(self, rows):
        self.say("flat_head")
        print("-" * 53)
        for row in rows:
            size = "{0}×{0}".format(row["n"])
            ratio = row["avg_ms_1d"] / row["avg_ms_2d"] if row["avg_ms_2d"] else 0.0
            print("{:<10}{:>11.6f}{:>15.6f}{:>15.2f}".format(size, row["avg_ms_2d"], row["avg_ms_1d"], ratio))


def read_matrix(console, name, n):
    """Read an n×n matrix line by line, re-prompting on bad input."""
    console.say("matrix_prompt", name=name, n=n)
    while True:
        rows = []
        while len(rows) < n:
            line = input()
            word = line.strip().lower()
            if not rows and word in ("cross", "x"):
                label = normalize_label(word)
                console.say("generated", label=label)
                return make_cross(n) if label == CROSS else make_x(n)
            if not word:
                console.say("err_rows", n=n, got=len(rows))
                rows = None
                break
            try:
                rows.append(parse_row(line, n))
            except NpuError as error:
                print(error.reason.render(console.lang))
        if rows is not None:
            return rows


def run_manual(console):
    """Mode 1: two 3×3 filters and a 3×3 pattern from the console."""
    n = 3
    console.section("sec_filter_input")
    filter_a = read_matrix(console, console.t("filter_a"), n)
    console.say("saved", name=console.t("filter_a"))
    console.matrix(filter_a)
    filter_b = read_matrix(console, console.t("filter_b"), n)
    console.say("saved", name=console.t("filter_b"))
    console.matrix(filter_b)

    console.section("sec_pattern_input")
    pattern = read_matrix(console, console.t("pattern"), n)
    console.say("saved", name=console.t("pattern"))
    console.matrix(pattern)

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    avg_ms = measure_ms(mac, pattern, filter_a)
    verdict = decide(score_a, score_b)

    console.section("sec_mac")
    console.say("score_a", score=repr(score_a))
    console.say("score_b", score=repr(score_b))
    console.say("time_avg", repeats=BENCH_REPEATS, ms=avg_ms)
    if verdict == UNDECIDED:
        verdict = console.t("verdict_tie", epsilon=EPSILON)
    console.say("verdict", verdict=verdict)

    console.section("sec_perf_3", repeats=BENCH_REPEATS)
    console.perf_table(benchmark(sizes=(3,)))


def resolve_data_path(console, requested):
    if requested:
        return requested
    if os.path.exists(DEFAULT_DATA) or not os.path.exists(SAMPLE_DATA):
        return DEFAULT_DATA
    console.say("using_sample", path=os.path.relpath(SAMPLE_DATA))
    return SAMPLE_DATA


def print_case(console, result):
    print("--- {} ---".format(result["id"]))
    if result["score_cross"] is not None:
        console.say("cross_score", score=repr(result["score_cross"]))
        console.say("x_score", score=repr(result["score_x"]))
    if result["decision"] is not None:
        status = "PASS" if result["passed"] else "FAIL"
        console.say("case_line", decision=result["decision"], expected=result["expected"], status=status)
    if not result["passed"]:
        console.say("case_failed", category=result["category"], reason=result["reason"].render(console.lang))


def run_dataset(console, data_path=None):
    """Mode 2: batch-classify a dataset and report the results."""
    path = resolve_data_path(console, data_path)
    console.say("dataset_path", path=os.path.relpath(path))
    results = []
    try:
        data = load_dataset(path)
    except NpuError as error:
        console.say("dataset_failed", category=error.category, reason=error.reason.render(console.lang))
    else:
        console.section("sec_filter_load")
        filters, filter_errors, results = analyze_dataset(data)
        for key in data["filters"]:
            if key in filters:
                console.say("filter_ok", group=key)
            else:
                console.say("filter_bad", group=key, reason=filter_errors[key].reason.render(console.lang))
        console.section("sec_patterns")
        for result in results:
            print_case(console, result)

    console.section("sec_perf", repeats=BENCH_REPEATS)
    console.perf_table(benchmark())
    console.section("sec_flat", repeats=BENCH_REPEATS)
    console.flat_table(benchmark_flat())

    console.section("sec_summary")
    summary = summarize(results)
    console.say("total", n=summary["total"])
    console.say("passed", n=summary["passed"])
    console.say("failed", n=summary["failed"])
    failures = [r for r in results if not r["passed"]]
    if failures:
        print()
        console.say("failures")
        for result in failures:
            print("- {} [{}]: {}".format(result["id"], result["category"], result["reason"].render(console.lang)))
    else:
        console.say("no_failures")
    print()
    console.say("detail_hint")
    return summary


def choose_mode(console):
    console.say("menu")
    while True:
        choice = input(console.t("choose")).strip()
        if choice in ("1", "2"):
            return choice
        console.say("menu_error")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mini NPU Simulator")
    parser.add_argument("--mode", choices=("1", "2"), help="skip the menu: 1 manual, 2 dataset")
    parser.add_argument("--lang", choices=("ko", "en"), default=os.environ.get("MINI_NPU_LANG", "ko"))
    parser.add_argument("--data", help="dataset path (default: data.json next to main.py)")
    args = parser.parse_args(argv)

    # Keep ✓ and × from crashing terminals that are not UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    console = Console(args.lang)
    console.say("title")
    print()
    try:
        mode = args.mode or choose_mode(console)
        if mode == "1":
            run_manual(console)
        else:
            run_dataset(console, args.data)
    except (EOFError, KeyboardInterrupt):
        print()
        console.say("bye")
    return 0


if __name__ == "__main__":
    sys.exit(main())
