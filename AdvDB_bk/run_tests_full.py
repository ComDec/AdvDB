#!/usr/bin/env python3
"""
Run all public tests in tests/ against root main.py with embedded expected results.
Style mirrors Final_Proj/run_tests.py but is self-contained (no imports).
Outputs PASS/FAIL per test and writes detailed logs to test_outputs/.
"""

import os
import re
import subprocess
import sys
from datetime import datetime

OUTPUT_DIR = "test_outputs"

TEST_CASES = {
    "test1": {
        "description": "First Committer Wins - T2 commits, T1 aborts",
        "expected_commits": ["T2"],
        "expected_aborts": ["T1"],
        "expected_dump": {"x1": 201, "x2": 202},
    },
    "test2": {
        "description": "Snapshot Isolation - Both commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20, "x1": 10},
        "expected_dump": {"x1": 101, "x2": 102},
    },
    "test3": {
        "description": "Site failure doesn't affect T1 - Both commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x3": 30},
    },
    "test3_5": {
        "description": "T2 aborts (wrote x8 before site 2 failed), T1 commits",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2"],
        "expected_reads": {"x3": 30},
    },
    "test3_7": {
        "description": "T2 aborts (wrote x8 before site 2 failed), T1 commits",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2"],
        "expected_reads": {"x3": 30},
    },
    "test4": {
        "description": "T1 aborts (site 2 failed after write), T2 ok",
        "expected_commits": ["T2"],
        "expected_aborts": ["T1"],
        "expected_reads": {"x3": 30, "x5": 50},
    },
    "test5": {
        "description": "T1 aborts (wrote x6 to site 2 which failed), T2 ok",
        "expected_commits": ["T2"],
        "expected_aborts": ["T1"],
        "expected_reads": {"x3": 30, "x5": 50},
    },
    "test6": {
        "description": "T1 ok, T2 ok - reads from recovered site",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10, "x3": 30},
    },
    "test7": {
        "description": "T2 reads initial x3=30 (snapshot isolation)",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10, "x2": 20, "x3": 30},
        "expected_dump": {"x3": 33},
    },
    "test8": {
        "description": "T2 reads x3=30, T3 reads x3=33",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10, "x2": 20},
    },
    "test9": {
        "description": "T3 reads x4=40, T1 reads x2=20",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x4": 40, "x2": 20},
    },
    "test10": {
        "description": "T3 reads x4=40, T1 reads x2=22",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x4": 40, "x2": 22},
    },
    "test11": {
        "description": "All should commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20},
    },
    "test12": {
        "description": "Both commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20},
        "expected_dump": {"x2": 10},
    },
    "test13": {
        "description": "Only T3 commits (first committer wins)",
        "expected_commits": ["T3"],
        "expected_aborts": ["T1", "T2"],
        "expected_dump": {"x2": 10},
    },
    "test14": {
        "description": "Only T1 commits (first committer wins)",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2", "T3"],
        "expected_dump": {"x2": 20},
    },
    "test15": {
        "description": "T1 aborts (site 2 failed), T2 commits, T3/T4/T5 abort (FCW)",
        "expected_commits": ["T2"],
        "expected_aborts": ["T1", "T3", "T4", "T5"],
        "expected_dump": {"x4": 44},
    },
    "test16": {
        "description": "All commit - T1 reads x2=22",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x4": 40, "x2": 22},
    },
    "test17": {
        "description": "T2 commits, T3 aborts (site 4 failed), T1 commits",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": ["T3"],
        "expected_reads": {"x3": 30, "x2": 20},
    },
    "test18": {
        "description": "RW Cycle - T5 aborts",
        "expected_commits": ["T1", "T2", "T3", "T4"],
        "expected_aborts": ["T5"],
        "expected_reads": {"x4": 40, "x5": 50, "x1": 10, "x2": 20, "x3": 30},
    },
    "test19": {
        "description": "T3 aborts (site 4 failed), others commit",
        "expected_commits": ["T1", "T2", "T4", "T5"],
        "expected_aborts": ["T3"],
    },
    "test20": {
        "description": "T1 commits, T2 aborts (FCW)",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2"],
        "expected_reads": {"x2": 20},
        "expected_dump": {"x2": 202},
    },
    "test21": {
        "description": "Simple RW cycle - T1 ok, T2 aborts",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2"],
        "expected_reads": {"x2": 20, "x4": 40},
        "expected_dump": {"x4": 30},
    },
    "test22": {
        "description": "T1 commits, T2 commits, T3 aborts (WW cycle)",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": ["T3"],
        "expected_reads": {"x4": 40, "x6": 60},
    },
    "test25": {
        "description": "T3 waits for site 2, then reads x8=88 and commits",
        "expected_commits": ["T1", "T2", "T3", "T4"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10, "x3": 30, "x8": 88},
    },
    "test26": {
        "description": "Read-only transactions always commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10, "x2": 20, "x3": 30, "x4": 40},
    },
    "test27": {
        "description": "Write to non-replicated var, its site fails -> abort",
        "expected_commits": [],
        "expected_aborts": ["T1"],
    },
    "test28": {
        "description": "Write to non-replicated var, different site fails -> commit",
        "expected_commits": ["T1"],
        "expected_aborts": [],
        "expected_dump": {"x1": 100},
    },
    "test29": {
        "description": "Three transactions write same var - first committer wins",
        "expected_commits": ["T2"],
        "expected_aborts": ["T1", "T3"],
        "expected_dump": {"x2": 200},
    },
    "test30": {
        "description": "Read your own write",
        "expected_commits": ["T1"],
        "expected_aborts": [],
        "expected_reads": {"x2": 999},
        "expected_dump": {"x2": 999},
    },
    "test31": {
        "description": "Snapshot isolation - T2 doesn't see T1's uncommitted write",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20},
        "expected_dump": {"x2": 999},
    },
    "test32": {
        "description": "Sites fail/recover, T2 reads from still-up sites",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20},
    },
    "test33": {
        "description": "Non-replicated var available immediately after recovery",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x3": 30},
    },
    "test34": {
        "description": "Write makes replicated var readable after recovery",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x2": 222},
        "expected_dump": {"x2": 222},
    },
    "test35": {
        "description": "Write to multiple vars, one site fails -> abort",
        "expected_commits": [],
        "expected_aborts": ["T1"],
    },
    "test36": {
        "description": "RW cycle - T1 commits first, T2 aborts",
        "expected_commits": ["T1"],
        "expected_aborts": ["T2"],
        "expected_reads": {"x2": 20, "x4": 40},
        "expected_dump": {"x4": 400},
    },
    "test37": {
        "description": "Disjoint writes - no conflict, both commit",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_dump": {"x1": 100, "x3": 300},
    },
    "test38": {
        "description": "Site fails after read (not write) - still commits",
        "expected_commits": ["T1"],
        "expected_aborts": [],
        "expected_reads": {"x1": 10},
    },
    "test39": {
        "description": "Complex ordering with snapshot isolation",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x2": 222},
        "expected_dump": {"x2": 222},
    },
    "test40": {
        "description": "Four transactions write same var - first committer wins",
        "expected_commits": ["T3"],
        "expected_aborts": ["T1", "T2", "T4"],
        "expected_dump": {"x4": 300},
    },
    "test41": {
        "description": "Site fails before write, recovers - commit ok",
        "expected_commits": ["T1"],
        "expected_aborts": [],
    },
    "test42": {
        "description": "Transaction waits for non-replicated var site",
        "expected_commits": ["T1"],
        "expected_aborts": [],
        "expected_reads": {"x3": 30},
    },
    "test43": {
        "description": "Chain of transactions with snapshot isolation",
        "expected_commits": ["T1", "T2", "T3"],
        "expected_aborts": [],
        "expected_reads": {"x2": 100},
        "expected_dump": {"x2": 200},
    },
    "test44": {
        "description": "All sites fail for replicated var - abort",
        "expected_commits": [],
        "expected_aborts": ["T1"],
    },
    "test45": {
        "description": "Write then fail then recover - still abort",
        "expected_commits": [],
        "expected_aborts": ["T1"],
    },
    "test_issue1": {
        "description": "Read site, site fails/recovers, then write - should commit (Issue 1 fix)",
        "expected_commits": ["T1"],
        "expected_aborts": [],
        "expected_reads": {"x2": 20},
        "expected_dump": {"x2": 222},
    },
    "test_issue2": {
        "description": "Sequential transactions - no RW cycle (Issue 2 fix)",
        "expected_commits": ["T1", "T2"],
        "expected_aborts": [],
        "expected_reads": {"x1": 100},
        "expected_dump": {"x1": 200},
    },
}


def run_test(test_name: str):
    """Run a single test and return raw output."""
    test_file = f"/data1/xw3763/project/playgroud/AdvDB/tests/{test_name}.txt"
    try:
        result = subprocess.run(
            ["python3", "main.py", test_file],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return result.stdout
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def parse_output(output: str):
    """Parse commits, aborts, reads, dump values from program output."""
    if not output or output == "TIMEOUT":
        return [], [], {}, {}

    lines = output.strip().splitlines()
    commits, aborts, reads, dump = [], [], {}, {}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if " commits" in stripped:
            commits.append(stripped.split()[0])
        elif " aborts" in stripped:
            aborts.append(stripped.split()[0])

        read_match = re.match(r"^(x\d+):\s*(-?\d+)$", stripped)
        if read_match:
            reads[read_match.group(1)] = int(read_match.group(2))

        dump_match = re.match(r"^site\s+\d+\s+-\s+(.+)$", stripped)
        if dump_match:
            tokens = dump_match.group(1).replace(",", " ").split()
            for i in range(0, len(tokens), 2):
                try:
                    var = tokens[i].rstrip(":")
                    val = int(tokens[i + 1].rstrip(","))
                    dump.setdefault(var, val)
                except (IndexError, ValueError):
                    break

    return commits, aborts, reads, dump


def check_results(output, test_info):
    """Compare actual output with expected outcomes."""
    if output is None:
        return False, ["Test file not found"], {}, {}, [], []
    if output == "TIMEOUT":
        return False, ["Test timed out"], {}, {}, [], []

    actual_commits, actual_aborts, actual_reads, actual_dump = parse_output(output)
    errors = []

    expected_commits = test_info.get("expected_commits", [])
    expected_aborts = test_info.get("expected_aborts", [])
    if set(actual_commits) != set(expected_commits):
        errors.append(f"Commits: expected {sorted(expected_commits)}, got {sorted(actual_commits)}")
    if set(actual_aborts) != set(expected_aborts):
        errors.append(f"Aborts: expected {sorted(expected_aborts)}, got {sorted(actual_aborts)}")

    for var, expected_val in test_info.get("expected_reads", {}).items():
        if var not in actual_reads:
            errors.append(f"Read {var}: expected {expected_val}, but no read found")
        elif actual_reads[var] != expected_val:
            errors.append(f"Read {var}: expected {expected_val}, got {actual_reads[var]}")

    for var, expected_val in test_info.get("expected_dump", {}).items():
        if var not in actual_dump:
            errors.append(f"Dump {var}: expected {expected_val}, but not in dump")
        elif actual_dump[var] != expected_val:
            errors.append(f"Dump {var}: expected {expected_val}, got {actual_dump[var]}")

    success = len(errors) == 0
    return success, errors, actual_reads, actual_dump, actual_commits, actual_aborts


def read_test_input(test_name):
    """Read test input file for logging."""
    path = f"/data1/xw3763/project/playgroud/AdvDB/tests/{test_name}.txt"
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "(Test file not found)"


def save_output_log(test_name, test_info, output, success, errors, actual_reads, actual_dump, actual_commits, actual_aborts):
    """Persist per-test details."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_file = os.path.join(OUTPUT_DIR, f"{test_name}_output.txt")
    with open(log_file, "w") as f:
        f.write("=" * 70 + "\n")
        f.write(f"TEST: {test_name}\n")
        f.write(f"Description: {test_info['description']}\n")
        f.write(f"Result: {'PASSED' if success else 'FAILED'}\n")
        f.write("=" * 70 + "\n\n")

        f.write("-" * 40 + "\n")
        f.write("COMMITS/ABORTS:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  Expected Commits: {test_info.get('expected_commits', [])}\n")
        f.write(f"  Actual Commits:   {actual_commits}\n")
        f.write(f"  Expected Aborts:  {test_info.get('expected_aborts', [])}\n")
        f.write(f"  Actual Aborts:    {actual_aborts}\n\n")

        expected_reads = test_info.get("expected_reads", {})
        if expected_reads or actual_reads:
            f.write("-" * 40 + "\n")
            f.write("READ VALUES:\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Expected Reads: {expected_reads}\n")
            f.write(f"  Actual Reads:   {actual_reads}\n\n")

        expected_dump = test_info.get("expected_dump", {})
        if expected_dump or actual_dump:
            f.write("-" * 40 + "\n")
            f.write("DUMP (Final State):\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Expected Dump: {expected_dump}\n")
            f.write(f"  Actual Dump:   {actual_dump}\n\n")

        if errors:
            f.write("-" * 40 + "\n")
            f.write("ERRORS:\n")
            f.write("-" * 40 + "\n")
            for err in errors:
                f.write(f"  - {err}\n")
            f.write("\n")

        f.write("-" * 40 + "\n")
        f.write("INPUT COMMANDS:\n")
        f.write("-" * 40 + "\n")
        f.write(read_test_input(test_name))
        f.write("\n\n")

        f.write("-" * 40 + "\n")
        f.write("FULL OUTPUT:\n")
        f.write("-" * 40 + "\n")
        f.write(output or "(No output)")
        f.write("\n")


def main():
    print("Running all tests...\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    passed = 0
    failed = 0
    failed_tests = []

    for test_name, test_info in TEST_CASES.items():
        output = run_test(test_name)
        success, errors, actual_reads, actual_dump, actual_commits, actual_aborts = check_results(output, test_info)
        save_output_log(test_name, test_info, output or "", success, errors, actual_reads, actual_dump, actual_commits, actual_aborts)

        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}: {test_info['description']}")
        if not success:
            for err in errors:
                print(f"    - {err}")
            failed += 1
            failed_tests.append(test_name)
        else:
            passed += 1

    summary_file = os.path.join(OUTPUT_DIR, "summary.txt")
    with open(summary_file, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("TEST SUMMARY\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total: {len(TEST_CASES)} tests\n")
        f.write(f"Passed: {passed}\n")
        f.write(f"Failed: {failed}\n\n")
        if failed_tests:
            f.write("Failed tests:\n")
            for t in failed_tests:
                f.write(f"  - {t}\n")
        else:
            f.write("All tests passed!\n")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")
    if failed_tests:
        print("Failed tests: " + ", ".join(failed_tests))
    print(f"\nOutput logs saved to: {OUTPUT_DIR}/")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
