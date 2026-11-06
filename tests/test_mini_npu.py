import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import main as npu  # noqa: E402

CROSS_3 = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
X_3 = [[1, 0, 1], [0, 1, 0], [1, 0, 1]]


def run_cli(lines, *argv):
    """Run main() with scripted stdin lines and return what it printed."""
    out = io.StringIO()
    with mock.patch("builtins.input", side_effect=list(lines) + [EOFError()]), contextlib.redirect_stdout(out):
        code = npu.main(list(argv))
    return code, out.getvalue()


def write_dataset(directory, payload):
    path = os.path.join(directory, "data.json")
    with open(path, "w", encoding="utf-8") as handle:
        if isinstance(payload, str):
            handle.write(payload)
        else:
            json.dump(payload, handle)
    return path


def dataset(**patterns):
    return {
        "filters": {"size_5": {"cross": npu.make_cross(5), "x": npu.make_x(5)}},
        "patterns": patterns,
    }


class MacTests(unittest.TestCase):
    def test_cross_on_cross(self):
        self.assertEqual(npu.mac(CROSS_3, CROSS_3), 5)

    def test_cross_on_x(self):
        self.assertEqual(npu.mac(CROSS_3, X_3), 1)

    def test_x_on_cross(self):
        self.assertEqual(npu.mac(X_3, CROSS_3), 1)

    def test_x_on_x(self):
        self.assertEqual(npu.mac(X_3, X_3), 5)

    def test_returns_float_for_real_values(self):
        self.assertIsInstance(npu.mac([[1]], [[2]]), float)
        self.assertAlmostEqual(npu.mac([[0.5, 0.25], [0, 1]], [[2, 4], [8, 0.5]]), 2.5)

    def test_supported_sizes(self):
        for n, cross_hits in ((5, 9), (13, 25), (25, 49)):
            with self.subTest(n=n):
                self.assertEqual(npu.mac(npu.make_cross(n), npu.make_cross(n)), cross_hits)
                self.assertEqual(npu.mac(npu.make_cross(n), npu.make_x(n)), 1)
                self.assertEqual(len(npu.validate_matrix(npu.make_x(n), n)), n)

    def test_flat_matches_nested(self):
        for n in npu.BENCH_SIZES:
            with self.subTest(n=n):
                p, f = npu.make_cross(n), npu.make_x(n)
                self.assertEqual(npu.mac_flat(npu.flatten(p), npu.flatten(f)), npu.mac(p, f))

    def test_generator_matches_assignment_patterns(self):
        self.assertEqual(npu.make_cross(3), CROSS_3)
        self.assertEqual(npu.make_x(3), X_3)


class InputValidationTests(unittest.TestCase):
    def test_valid_row(self):
        self.assertEqual(npu.parse_row(" 1 2.5   -3e-1 ", 3), [1.0, 2.5, -0.3])

    def test_wrong_column_count(self):
        for line in ("1 2", "1 2 3 4"):
            with self.subTest(line=line), self.assertRaises(npu.NpuError) as caught:
                npu.parse_row(line, 3)
            self.assertEqual(caught.exception.category, npu.CAT_SIZE)

    def test_number_parse_failure(self):
        with self.assertRaises(npu.NpuError) as caught:
            npu.parse_row("1 two 3", 3)
        self.assertEqual(caught.exception.reason.key, "err_number")

    def test_rejects_non_finite_text(self):
        for token in ("nan", "inf", "-Infinity"):
            with self.subTest(token=token), self.assertRaises(npu.NpuError):
                npu.parse_row("1 2 " + token, 3)

    def test_validate_matrix_wrong_rows(self):
        with self.assertRaises(npu.NpuError) as caught:
            npu.validate_matrix([[1, 2, 3]] * 2, 3)
        self.assertEqual((caught.exception.category, caught.exception.reason.key), (npu.CAT_SIZE, "r_rows"))

    def test_validate_matrix_wrong_columns(self):
        with self.assertRaises(npu.NpuError) as caught:
            npu.validate_matrix([[1, 2, 3], [1, 2], [1, 2, 3]], 3)
        self.assertEqual(caught.exception.reason.key, "r_columns")

    def test_validate_matrix_rejects_bad_cells(self):
        for bad in ("1", None, True, float("nan"), float("inf"), 10 ** 400):
            with self.subTest(bad=bad), self.assertRaises(npu.NpuError) as caught:
                npu.validate_matrix([[bad]], 1)
            self.assertEqual(caught.exception.category, npu.CAT_SCHEMA)

    def test_validate_matrix_rejects_non_lists(self):
        for bad in ("abc", {"a": 1}, [1, 2]):
            with self.subTest(bad=bad), self.assertRaises(npu.NpuError):
                npu.validate_matrix(bad, 2)


class LabelTests(unittest.TestCase):
    def test_required_mappings(self):
        cases = {"+": npu.CROSS, "x": npu.X, "cross": npu.CROSS}
        for raw, canonical in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(npu.normalize_label(raw), canonical)

    def test_case_and_whitespace_policy(self):
        for raw, canonical in ((" CROSS ", npu.CROSS), ("X", npu.X), ("\t+\n", npu.CROSS)):
            with self.subTest(raw=raw):
                self.assertEqual(npu.normalize_label(raw), canonical)

    def test_unsupported_labels(self):
        for raw in ("o", "", "plus", 1, None, ["x"]):
            with self.subTest(raw=raw), self.assertRaises(npu.NpuError) as caught:
                npu.normalize_label(raw)
            self.assertEqual(caught.exception.category, npu.CAT_LABEL)


class EpsilonTests(unittest.TestCase):
    def test_exact_tie(self):
        self.assertEqual(npu.decide(5.0, 5.0), npu.UNDECIDED)

    def test_within_epsilon(self):
        self.assertNotEqual(0.1 + 0.2 + 0.6, 0.3 + 0.3 + 0.3)
        self.assertEqual(npu.decide(0.1 + 0.2 + 0.6, 0.3 + 0.3 + 0.3), npu.UNDECIDED)

    def test_outside_epsilon(self):
        self.assertEqual(npu.decide(1.0 + 2e-9, 1.0), "A")
        self.assertEqual(npu.decide(1.0, 1.0 + 2e-9), "B")

    def test_boundary_is_not_a_tie(self):
        self.assertEqual(npu.decide(1.0, 0.0, epsilon=1.0), "A")

    def test_custom_labels(self):
        self.assertEqual(npu.decide(5.0, 1.0, npu.CROSS, npu.X), npu.CROSS)
        self.assertEqual(npu.decide(1.0, 5.0, npu.CROSS, npu.X), npu.X)


class DatasetLoadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def assert_load_fails(self, payload, key):
        with self.assertRaises(npu.NpuError) as caught:
            npu.load_dataset(write_dataset(self.tmp.name, payload))
        self.assertEqual(caught.exception.category, npu.CAT_SCHEMA)
        self.assertEqual(caught.exception.reason.key, key)

    def test_syntax_error(self):
        self.assert_load_fails('{"filters": ', "r_json_syntax")

    def test_missing_file(self):
        with self.assertRaises(npu.NpuError) as caught:
            npu.load_dataset(os.path.join(self.tmp.name, "nope.json"))
        self.assertEqual(caught.exception.reason.key, "r_file_missing")

    def test_top_level_not_object(self):
        self.assert_load_fails("[1, 2]", "r_top_not_object")

    def test_missing_top_level_fields(self):
        self.assert_load_fails({"patterns": {}}, "r_top_missing")
        self.assert_load_fails({"filters": {}}, "r_top_missing")

    def test_top_level_field_wrong_type(self):
        self.assert_load_fails({"filters": [], "patterns": {}}, "r_field_not_object")

    def test_accepts_utf8_bom(self):
        path = write_dataset(self.tmp.name, "﻿" + json.dumps(dataset()))
        self.assertIn("filters", npu.load_dataset(path))


class CaseAnalysisTests(unittest.TestCase):
    def analyze(self, patterns, filters=None):
        data = {
            "filters": filters or {"size_5": {"cross": npu.make_cross(5), "x": npu.make_x(5)}},
            "patterns": patterns,
        }
        return npu.analyze_dataset(data)[2]

    def one(self, case, key="size_5_1", filters=None):
        return self.analyze({key: case}, filters)[0]

    def test_pass_with_normalized_expected(self):
        for label, matrix, canonical in (("+", npu.make_cross(5), npu.CROSS), ("x", npu.make_x(5), npu.X)):
            with self.subTest(label=label):
                result = self.one({"input": matrix, "expected": label})
                self.assertTrue(result["passed"])
                self.assertEqual((result["decision"], result["expected"]), (canonical, canonical))

    def test_scores_recorded(self):
        result = self.one({"input": npu.make_cross(5), "expected": "+"})
        self.assertEqual((result["score_cross"], result["score_x"]), (9.0, 1.0))

    def test_size_mismatch_fails_case(self):
        result = self.one({"input": npu.make_cross(4), "expected": "+"})
        self.assertEqual((result["passed"], result["category"]), (False, npu.CAT_SIZE))

    def test_missing_fields_fail_case(self):
        for case, field in (({"expected": "+"}, "input"), ({"input": npu.make_cross(5)}, "expected")):
            with self.subTest(field=field):
                result = self.one(case)
                self.assertEqual(result["category"], npu.CAT_SCHEMA)
                self.assertEqual(result["reason"].params["field"], field)

    def test_case_not_object(self):
        self.assertEqual(self.one([1, 2, 3])["reason"].key, "r_case_not_object")

    def test_bad_key(self):
        for key in ("pattern_1", "size_x_1", "size_5", "size_0_1"):
            with self.subTest(key=key):
                self.assertEqual(self.one({"input": [], "expected": "+"}, key=key)["reason"].key, "r_case_key")

    def test_missing_filter_group(self):
        result = self.one({"input": npu.make_cross(7), "expected": "+"}, key="size_7_1")
        self.assertEqual(result["reason"].key, "r_group_missing")

    def test_unsupported_label_fails_case(self):
        result = self.one({"input": npu.make_cross(5), "expected": "o"})
        self.assertEqual(result["category"], npu.CAT_LABEL)

    def test_tie_fails_with_numeric_category(self):
        matrix = [[0.0] * 5 for _ in range(5)]
        for i, cross_value, x_value in ((0, 0.1, 0.3), (1, 0.2, 0.3), (3, 0.6, 0.3)):
            matrix[i][2] = cross_value
            matrix[i][i] = x_value
        result = self.one({"input": matrix, "expected": "x"})
        self.assertEqual(result["decision"], npu.UNDECIDED)
        self.assertEqual((result["passed"], result["category"]), (False, npu.CAT_NUMERIC))

    def test_wrong_decision_fails_with_logic_category(self):
        result = self.one({"input": npu.make_x(5), "expected": "+"})
        self.assertEqual((result["decision"], result["category"]), (npu.X, npu.CAT_LOGIC))

    def test_overflowing_score_fails_instead_of_deciding(self):
        matrix = [[1e308] * 5 for _ in range(5)]
        result = self.one({"input": matrix, "expected": "+"})
        self.assertEqual((result["passed"], result["category"]), (False, npu.CAT_NUMERIC))

    def test_filter_size_mismatch_marks_only_that_group(self):
        filters = {
            "size_5": {"cross": npu.make_cross(4), "x": npu.make_x(5)},
            "size_13": {"cross": npu.make_cross(13), "x": npu.make_x(13)},
        }
        results = self.analyze({
            "size_5_1": {"input": npu.make_cross(5), "expected": "+"},
            "size_13_1": {"input": npu.make_cross(13), "expected": "+"},
        }, filters)
        self.assertEqual((results[0]["passed"], results[0]["category"]), (False, npu.CAT_SIZE))
        self.assertEqual(results[0]["reason"].key, "r_group_broken")
        self.assertTrue(results[1]["passed"])

    def test_filter_labels_normalized(self):
        filters = {"size_5": {"Cross": npu.make_cross(5), " X ": npu.make_x(5)}}
        self.assertTrue(self.one({"input": npu.make_x(5), "expected": "x"}, filters=filters)["passed"])

    def test_filter_group_incomplete_or_duplicate(self):
        for group, key in (
            ({"cross": npu.make_cross(5)}, "r_group_labels"),
            ({"cross": npu.make_cross(5), "CROSS": npu.make_cross(5), "x": npu.make_x(5)}, "r_group_duplicate"),
        ):
            with self.subTest(key=key):
                filters, errors = npu.load_filters({"size_5": group})
                self.assertEqual(errors["size_5"].reason.key, key)
                self.assertEqual(filters, {})

    def test_summary_totals(self):
        results = self.analyze({
            "size_5_1": {"input": npu.make_cross(5), "expected": "+"},
            "size_5_2": {"input": npu.make_x(5), "expected": "x"},
            "size_5_3": {"input": npu.make_x(5), "expected": "+"},
            "size_5_4": {"expected": "+"},
        })
        summary = npu.summarize(results)
        self.assertEqual(summary, {"total": 4, "passed": 2, "failed": 2})
        self.assertEqual(summary["passed"] + summary["failed"], summary["total"])

    def test_reasons_render_in_both_languages(self):
        result = self.one({"input": npu.make_cross(4), "expected": "+"})
        self.assertIn("행 수", result["reason"].render("ko"))
        self.assertIn("Row count", result["reason"].render("en"))


class BenchmarkTests(unittest.TestCase):
    def test_times_at_least_ten_runs(self):
        calls = []
        npu.measure_ms(lambda: calls.append(1))
        self.assertGreaterEqual(len(calls), 10)
        self.assertGreaterEqual(npu.BENCH_REPEATS, 10)

    def test_measure_averages_the_clock(self):
        ticks = iter(range(0, 40, 1))
        with mock.patch.object(npu.time, "perf_counter_ns", lambda: next(ticks) * 1000000):
            self.assertEqual(npu.measure_ms(lambda: None, repeats=4), 1.0)

    def test_rejects_zero_repeats(self):
        with self.assertRaises(ValueError):
            npu.measure_ms(lambda: None, repeats=0)

    def test_table_covers_required_sizes(self):
        rows = npu.benchmark()
        self.assertEqual([r["n"] for r in rows], [3, 5, 13, 25])
        self.assertEqual([r["mac_count"] for r in rows], [9, 25, 169, 625])
        for row in rows:
            self.assertGreater(row["avg_ms"], 0)


class ConsoleFlowTests(unittest.TestCase):
    CROSS_LINES = ["0 1 0", "1 1 1", "0 1 0"]
    X_LINES = ["1 0 1", "0 1 0", "1 0 1"]

    def test_mode_1_assignment_example(self):
        lines = ["1"] + self.CROSS_LINES + self.X_LINES + self.X_LINES
        code, out = run_cli(lines)
        self.assertEqual(code, 0)
        self.assertIn("A 점수: 1.0", out)
        self.assertIn("B 점수: 5.0", out)
        self.assertIn("판정: B", out)
        self.assertIn("3×3", out)

    def test_mode_1_recovers_from_bad_input(self):
        lines = ["9", "1", "0 1", "a b c"] + self.CROSS_LINES + self.X_LINES + ["1 1"] + self.CROSS_LINES
        code, out = run_cli(lines)
        self.assertEqual(code, 0)
        self.assertIn("1 또는 2", out)
        self.assertIn("각 줄에 3개의 숫자", out)
        self.assertIn("숫자로 변환할 수 없는", out)
        self.assertIn("판정: A", out)

    def test_mode_1_blank_line_restarts_matrix(self):
        lines = ["1", "0 1 0", ""] + self.CROSS_LINES + self.X_LINES + self.CROSS_LINES
        _, out = run_cli(lines)
        self.assertIn("1개 행만", out)
        self.assertIn("판정: A", out)

    def test_mode_1_tie_is_undecided(self):
        a = ["0.1 0.2 0.6", "0 0 0", "0 0 0"]
        b = ["0.3 0.3 0.3", "0 0 0", "0 0 0"]
        pattern = ["1 1 1", "1 1 1", "1 1 1"]
        _, out = run_cli(["1"] + a + b + pattern)
        self.assertIn("판정 불가", out)

    def test_mode_1_generator_shortcut(self):
        _, out = run_cli(["1", "cross", "x", "cross"])
        self.assertIn("A 점수: 5.0", out)
        self.assertIn("B 점수: 1.0", out)

    def test_eof_exits_cleanly(self):
        code, out = run_cli([])
        self.assertEqual(code, 0)
        self.assertIn("종료", out)

    def test_english_output(self):
        _, out = run_cli(["1", "cross", "x", "x"], "--lang", "en")
        self.assertIn("Score B: 5.0", out)
        self.assertIn("Decision: B", out)

    def test_mode_2_reports_totals_and_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_dataset(tmp, dataset(
                size_5_1={"input": npu.make_cross(5), "expected": "+"},
                size_5_2={"input": npu.make_cross(4), "expected": "+"},
            ))
            code, out = run_cli([], "--mode", "2", "--data", path)
        self.assertEqual(code, 0)
        self.assertIn("총 테스트: 2개", out)
        self.assertIn("통과: 1개", out)
        self.assertIn("실패: 1개", out)
        self.assertIn("- size_5_2 [MATRIX SIZE]", out)
        self.assertIn("25×25", out)

    def test_mode_2_survives_broken_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli([], "--mode", "2", "--data", write_dataset(tmp, "{oops"))
        self.assertEqual(code, 0)
        self.assertIn("JSON 문법 오류", out)
        self.assertIn("총 테스트: 0개", out)


class FixtureTests(unittest.TestCase):
    def test_fixture_outcomes(self):
        results = npu.analyze_dataset(npu.load_dataset(npu.SAMPLE_DATA))[2]
        by_id = {r["id"]: r for r in results}
        self.assertEqual(npu.summarize(results), {"total": 16, "passed": 8, "failed": 8})
        expected = {
            "size_13_3": npu.CAT_NUMERIC,
            "size_5_4": npu.CAT_SIZE,
            "size_5_5": npu.CAT_LABEL,
            "size_5_6": npu.CAT_LOGIC,
            "size_13_4": npu.CAT_SCHEMA,
            "size_25_4": npu.CAT_SCHEMA,
            "size_7_1": npu.CAT_SCHEMA,
            "pattern_1": npu.CAT_SCHEMA,
        }
        failed = {r["id"]: r["category"] for r in results if not r["passed"]}
        self.assertEqual(failed, expected)
        self.assertTrue(by_id["size_25_3"]["passed"])


if __name__ == "__main__":
    unittest.main()
