#!/usr/bin/env python3
"""Run the unit tests and print what each one checks, with its result.

    python tests/report.py
    python tests/report.py --lang en
"""

import argparse
import os
import platform
import sys
import time
import unittest

import test_mini_npu

GROUPS = (
    ("MacTests", "MAC 연산", "MAC operation", "같은 위치를 곱해 모두 더한 점수가 맞는가", "Is the sum of position-wise products correct?"),
    ("InputValidationTests", "입력 검증", "Input validation", "잘못된 입력을 계산 전에 걸러 내는가", "Is bad input caught before computing?"),
    ("LabelTests", "라벨 정규화", "Label normalization", "여러 표기를 Cross와 X로 통일하는가", "Do different spellings become Cross and X?"),
    ("EpsilonTests", "ε 동점 판정", "ε tie rule", "오차 안의 차이를 동점으로 처리하는가", "Is a difference within the error treated as a tie?"),
    ("DatasetLoadTests", "데이터 파일 읽기", "Loading the data file", "망가진 파일에도 이유를 밝히고 실패하는가", "Does a broken file fail with a stated reason?"),
    ("CaseAnalysisTests", "케이스 분석", "Case analysis", "케이스의 오류가 그 케이스의 FAIL로 끝나는가", "Does an error stay as that case's FAIL?"),
    ("BenchmarkTests", "성능 측정", "Performance measurement", "시간과 연산 횟수를 요구대로 재는가", "Are time and operation count measured as required?"),
    ("ConsoleFlowTests", "콘솔 실행 흐름", "Console flow", "실제 입출력이 끝까지 올바르게 이어지는가", "Does real input and output work from start to end?"),
    ("FixtureTests", "데모 데이터", "Demo data", "다섯 실패 범주가 의도대로 나오는가", "Do the five failure categories appear as intended?"),
    ("ProvidedDataTests", "제공 데이터", "Provided data", "data.json의 결과가 그대로 재현되는가", "Are the data.json results reproduced?"),
)

CHECKS = {
    "test_cross_on_cross": ("Cross 패턴 × Cross 필터의 점수는 5", "Cross pattern × Cross filter scores 5"),
    "test_cross_on_x": ("Cross 패턴 × X 필터의 점수는 1", "Cross pattern × X filter scores 1"),
    "test_x_on_cross": ("X 패턴 × Cross 필터의 점수는 1", "X pattern × Cross filter scores 1"),
    "test_x_on_x": ("X 패턴 × X 필터의 점수는 5", "X pattern × X filter scores 5"),
    "test_returns_float_for_real_values": ("소수 입력도 계산해 float를 돌려준다", "Decimal input works and returns a float"),
    "test_supported_sizes": ("5, 13, 25 크기의 점수가 9, 25, 49와 1이다", "Sizes 5, 13, 25 score 9, 25, 49 and 1"),
    "test_flat_matches_nested": ("1차원 MAC과 2차원 MAC의 결과가 같다", "1D MAC equals 2D MAC"),
    "test_generator_matches_assignment_patterns": ("생성기가 과제의 3×3 Cross와 X를 만든다", "The generator builds the assignment's 3×3 Cross and X"),
    "test_valid_row": ("정수, 소수, 지수 표기가 섞인 줄을 읽는다", "Reads a row mixing integers, decimals and exponents"),
    "test_wrong_column_count": ("칸 수가 다른 줄은 MATRIX SIZE 오류다", "A row with the wrong count is a MATRIX SIZE error"),
    "test_number_parse_failure": ("숫자가 아닌 값은 숫자 변환 오류다", "A non-number is a number conversion error"),
    "test_rejects_non_finite_text": ("nan과 inf 입력을 거부한다", "Rejects nan and inf input"),
    "test_validate_matrix_wrong_rows": ("행 수가 다르면 거부한다", "Rejects the wrong row count"),
    "test_validate_matrix_wrong_columns": ("열 수가 다른 행이 있으면 거부한다", "Rejects a row with the wrong column count"),
    "test_validate_matrix_rejects_bad_cells": ("문자, None, bool, nan, inf, 너무 큰 값을 거부한다", "Rejects strings, None, bool, nan, inf and huge values"),
    "test_validate_matrix_rejects_non_lists": ("리스트가 아닌 행렬을 거부한다", "Rejects a matrix that is not a list of lists"),
    "test_required_mappings": ("+는 Cross, x는 X, cross는 Cross가 된다", "+ becomes Cross, x becomes X, cross becomes Cross"),
    "test_case_and_whitespace_policy": ("대소문자와 앞뒤 공백을 무시한다", "Ignores letter case and surrounding spaces"),
    "test_unsupported_labels": ("o, 빈 문자열, 숫자 같은 라벨은 추측하지 않고 거부한다", "Rejects labels such as o, empty or numbers, without guessing"),
    "test_exact_tie": ("5.0과 5.0은 UNDECIDED다", "5.0 and 5.0 are UNDECIDED"),
    "test_within_epsilon": ("0.1+0.2+0.6과 0.3+0.3+0.3은 ==로 다르지만 UNDECIDED다", "0.1+0.2+0.6 and 0.3+0.3+0.3 differ under == but are UNDECIDED"),
    "test_outside_epsilon": ("차이가 2e-9면 큰 쪽을 고른다", "A difference of 2e-9 picks the larger score"),
    "test_boundary_is_not_a_tie": ("차이가 ε과 정확히 같으면 동점이 아니다", "A difference exactly equal to ε is not a tie"),
    "test_custom_labels": ("판정 결과에 지정한 라벨을 돌려준다", "Returns the labels it was given"),
    "test_syntax_error": ("JSON 문법 오류를 알린다", "Reports a JSON syntax error"),
    "test_missing_file": ("파일이 없음을 알린다", "Reports a missing file"),
    "test_top_level_not_object": ("맨 위가 객체가 아니면 알린다", "Reports a top level that is not an object"),
    "test_missing_top_level_fields": ("filters나 patterns가 없으면 알린다", "Reports missing filters or patterns"),
    "test_top_level_field_wrong_type": ("filters의 형식이 틀리면 알린다", "Reports filters of the wrong type"),
    "test_accepts_utf8_bom": ("UTF-8 BOM이 붙은 파일도 읽는다", "Reads a file that starts with a UTF-8 BOM"),
    "test_pass_with_normalized_expected": ("expected의 +와 x를 정규화해 PASS한다", "Normalizes expected + and x, and passes"),
    "test_scores_recorded": ("5×5 Cross의 두 점수 9.0과 1.0을 기록한다", "Records the 5×5 Cross scores 9.0 and 1.0"),
    "test_size_mismatch_fails_case": ("크기가 다른 입력은 MATRIX SIZE로 FAIL한다", "A wrong-sized input FAILs as MATRIX SIZE"),
    "test_missing_fields_fail_case": ("input이나 expected가 없으면 DATA / SCHEMA로 FAIL한다", "Missing input or expected FAILs as DATA / SCHEMA"),
    "test_case_not_object": ("케이스가 객체가 아니면 FAIL한다", "A case that is not an object FAILs"),
    "test_bad_key": ("size_N_idx 형식이 아닌 키는 FAIL한다", "A key not shaped like size_N_idx FAILs"),
    "test_missing_filter_group": ("맞는 크기의 필터가 없으면 FAIL한다", "No filter of that size FAILs"),
    "test_unsupported_label_fails_case": ("모르는 라벨은 LABEL NORMALIZATION으로 FAIL한다", "An unknown label FAILs as LABEL NORMALIZATION"),
    "test_tie_fails_with_numeric_category": ("동점은 NUMERICAL COMPARISON으로 FAIL한다", "A tie FAILs as NUMERICAL COMPARISON"),
    "test_wrong_decision_fails_with_logic_category": ("판정이 정답과 다르면 CLASSIFICATION LOGIC으로 FAIL한다", "A wrong decision FAILs as CLASSIFICATION LOGIC"),
    "test_overflowing_score_fails_instead_of_deciding": ("점수가 넘치면 판정하지 않고 FAIL한다", "An overflowing score FAILs without a decision"),
    "test_filter_size_mismatch_marks_only_that_group": ("망가진 필터는 그 크기의 케이스만 FAIL시킨다", "A broken filter FAILs only the cases of that size"),
    "test_filter_labels_normalized": ("필터 키의 라벨도 정규화한다", "Filter key labels are normalized too"),
    "test_filter_group_incomplete_or_duplicate": ("필터가 빠지거나 중복되면 그룹 오류다", "A missing or duplicate filter is a group error"),
    "test_summary_totals": ("통과와 실패의 합이 전체와 같다", "Passed plus failed equals the total"),
    "test_reasons_render_in_both_languages": ("실패 이유가 한국어와 영어로 나온다", "Failure reasons render in Korean and English"),
    "test_times_at_least_ten_runs": ("최소 10회 측정한다", "Measures at least 10 runs"),
    "test_measure_averages_the_clock": ("측정값이 평균 밀리초다", "The measurement is the mean in milliseconds"),
    "test_rejects_zero_repeats": ("반복 0회를 거부한다", "Rejects zero repeats"),
    "test_table_covers_required_sizes": ("크기 3, 5, 13, 25와 연산 9, 25, 169, 625를 낸다", "Gives sizes 3, 5, 13, 25 and counts 9, 25, 169, 625"),
    "test_mode_1_assignment_example": ("Mode 1: A 1.0, B 5.0, 판정 B를 출력한다", "Mode 1 prints A 1.0, B 5.0, decision B"),
    "test_mode_1_recovers_from_bad_input": ("Mode 1: 틀린 메뉴와 입력을 안내하고 끝까지 진행한다", "Mode 1 explains a bad menu choice and bad input, then finishes"),
    "test_mode_1_blank_line_restarts_matrix": ("Mode 1: 빈 줄이면 그 행렬을 다시 받는다", "Mode 1 restarts the matrix after a blank line"),
    "test_mode_1_tie_is_undecided": ("Mode 1: 동점이면 판정 불가를 출력한다", "Mode 1 prints undecided on a tie"),
    "test_mode_1_generator_shortcut": ("Mode 1: cross와 x 입력으로 배열을 만든다", "Mode 1 generates arrays from cross and x"),
    "test_eof_exits_cleanly": ("입력이 끊겨도 오류 없이 끝난다", "Ends cleanly when input stops"),
    "test_english_output": ("--lang en이면 영어로 출력한다", "--lang en prints English"),
    "test_mode_2_reports_totals_and_failures": ("Mode 2: 합계, 실패 이유, 성능 표를 출력한다", "Mode 2 prints totals, failure reasons and the performance table"),
    "test_mode_2_survives_broken_file": ("Mode 2: 망가진 파일에도 멈추지 않는다", "Mode 2 survives a broken file"),
    "test_fixture_outcomes": ("16개 중 8개 통과, 실패 8개의 범주가 정확하다", "8 of 16 pass, and all 8 failure categories are right"),
    "test_provided_data_outcomes": ("6개 중 3개 통과, 나머지 3개는 동점이라 UNDECIDED다", "3 of 6 pass; the other 3 are ties, so UNDECIDED"),
}

ORDER = {method: position for position, method in enumerate(CHECKS)}

TEXT = {
    "ko": {
        "title": "=== Mini NPU 단위 테스트 ===",
        "group": "# [{index}] {name} ({passed}/{total} 통과)",
        "summary": "# 요약",
        "total": "전체 {total}개, 통과 {passed}개, 실패 {failed}개, 건너뜀 {skipped}개 ({seconds:.3f}초)",
        "ok": "결과: 모두 통과",
        "bad": "결과: 실패가 있습니다",
    },
    "en": {
        "title": "=== Mini NPU unit tests ===",
        "group": "# [{index}] {name} ({passed}/{total} passed)",
        "summary": "# Summary",
        "total": "{total} total, {passed} passed, {failed} failed, {skipped} skipped ({seconds:.3f} s)",
        "ok": "Result: all passed",
        "bad": "Result: there are failures",
    },
}

LINE = "#" + "-" * 39


class ReportResult(unittest.TestResult):
    """Keep one outcome per test method; a failed subtest fails its method."""

    def __init__(self):
        super().__init__()
        self.outcomes = {}

    def startTest(self, test):
        super().startTest(test)
        self.outcomes[test.id()] = ("PASS", "")

    def _fail(self, test, err):
        message = str(err[1]).strip().splitlines()
        self.outcomes[test.id()] = ("FAIL", message[0] if message else err[0].__name__)

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._fail(test, err)

    def addError(self, test, err):
        super().addError(test, err)
        self._fail(test, err)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._fail(test, err)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = ("SKIP", reason)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Unit test report")
    parser.add_argument("--lang", choices=("ko", "en"), default=os.environ.get("MINI_NPU_LANG", "ko"))
    args = parser.parse_args(argv)
    index = 0 if args.lang == "ko" else 1
    text = TEXT[args.lang]

    suite = unittest.defaultTestLoader.loadTestsFromModule(test_mini_npu)
    result = ReportResult()
    started = time.perf_counter()
    suite.run(result)
    seconds = time.perf_counter() - started

    by_group = {}
    for test_id, outcome in result.outcomes.items():
        _, group, method = test_id.rsplit(".", 2)
        by_group.setdefault(group, []).append((method, outcome))

    print(text["title"])
    print("Python {} · tests/test_mini_npu.py".format(platform.python_version()))
    rows = []
    for number, (group, name_ko, name_en, aim_ko, aim_en) in enumerate(GROUPS, start=1):
        tests = sorted(by_group.pop(group, []), key=lambda item: ORDER.get(item[0], len(ORDER)))
        name = (name_ko, name_en)[index]
        passed = sum(1 for _, outcome in tests if outcome[0] == "PASS")
        rows.append((passed, len(tests), name))
        print()
        print(LINE)
        print(text["group"].format(index=number, name=name, passed=passed, total=len(tests)))
        print("# " + (aim_ko, aim_en)[index])
        print(LINE)
        for method, (status, detail) in tests:
            print("{:<5} {}".format(status, CHECKS[method][index] if method in CHECKS else method))
            if detail:
                print("      " + detail)
    if by_group:
        raise SystemExit("Test classes missing from GROUPS: " + ", ".join(sorted(by_group)))

    outcomes = [outcome[0] for outcome in result.outcomes.values()]
    failed = outcomes.count("FAIL")
    print()
    print(LINE)
    print(text["summary"])
    print(LINE)
    for passed, total, name in rows:
        print("{:>2}/{:<2}  {}".format(passed, total, name))
    print()
    print(text["total"].format(
        total=len(outcomes), passed=outcomes.count("PASS"), failed=failed,
        skipped=outcomes.count("SKIP"), seconds=seconds,
    ))
    print(text["bad"] if failed else text["ok"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
