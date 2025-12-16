#!/usr/bin/env python3
"""
Run all public tests under tests/ using the root main.py and verify results
against the expectations defined in Final_Proj/run_tests.py.
"""

import re
import subprocess
import sys
from Final_Proj.run_tests import TEST_CASES


def parse_output(output: str):
    """Extract commits, aborts, reads, and dump values from program output."""
    commits, aborts, reads, dump = [], [], {}, {}
    if not output:
        return commits, aborts, reads, dump

    for raw_line in output.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if " commits" in line:
            commits.append(line.split()[0])
        elif " aborts" in line:
            tx = line.split()[0]
            if tx not in aborts:
                aborts.append(tx)

        read_match = re.match(r"^(x\d+):\s*(-?\d+)$", line)
        if read_match:
            reads[read_match.group(1)] = int(read_match.group(2))

        dump_match = re.match(r"^site\s+\d+\s+-\s+(.+)$", line)
        if dump_match:
            tokens = dump_match.group(1).split()
            for i in range(0, len(tokens), 2):
                try:
                    var = tokens[i].rstrip(":")
                    val = int(tokens[i + 1])
                    dump.setdefault(var, val)
                except (IndexError, ValueError):
                    break

    return commits, aborts, reads, dump


def check_test(test_name: str, info: dict):
    """Run one test file and compare results to expectations."""
    proc = subprocess.run(
        ["python3", "main.py", f"tests/{test_name}.txt"],
        capture_output=True,
        text=True,
    )
    commits, aborts, reads, dump = parse_output(proc.stdout)

    errors = []
    expected_commits = info.get("expected_commits", [])
    expected_aborts = info.get("expected_aborts", [])
    if set(commits) != set(expected_commits):
        errors.append(f"Commits: expected {sorted(expected_commits)}, got {sorted(commits)}")
    if set(aborts) != set(expected_aborts):
        errors.append(f"Aborts: expected {sorted(expected_aborts)}, got {sorted(aborts)}")

    for var, expected_val in info.get("expected_reads", {}).items():
        if var not in reads:
            errors.append(f"Read {var}: expected {expected_val}, missing")
        elif reads[var] != expected_val:
            errors.append(f"Read {var}: expected {expected_val}, got {reads[var]}")

    for var, expected_val in info.get("expected_dump", {}).items():
        if var not in dump:
            errors.append(f"Dump {var}: expected {expected_val}, missing")
        elif dump[var] != expected_val:
            errors.append(f"Dump {var}: expected {expected_val}, got {dump[var]}")

    return errors, proc.stdout


def main():
    print("Running all public tests against main.py...\n")
    failed = []

    for test_name, info in TEST_CASES.items():
        errors, _ = check_test(test_name, info)
        status = "PASS" if not errors else "FAIL"
        print(f"{status} {test_name}: {info['description']}")
        for err in errors:
            print(f"  - {err}")
        if errors:
            failed.append(test_name)

    print("\nSummary")
    print("=======")
    print(f"Total: {len(TEST_CASES)}")
    print(f"Passed: {len(TEST_CASES) - len(failed)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print("Failed tests: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
