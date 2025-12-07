# Expected Outputs (Simplified)

Quick reference for provided test scripts; exact site dumps may list all variables, but key outcomes are noted.

- `test_basic.txt`: T1/T2 commit; x1=101 at site2, x2=202 at all sites; dump shows updated values.
- `test_ww_conflict.txt`: T1 commits x1=100 (site2); T2 aborts on WW conflict.
- `test_rw_conflict.txt`: T2 commits x2=202; T1 commits x4=104; demonstrates SSI RW handling.
- `test_snapshot.txt`: T1 commits x1=101, x2=102; T2 reads old snapshot values (x1=10, x2=20) and commits.
- `test_site_failure.txt`: After site2 fail/recover, T2 reads x4 successfully; no aborts.
- `test_replicated.txt`: T1 commits even-variable writes to all sites; after site1/2 fail, T2 reads replicated values (202/204) and commits.
- `test_readonly.txt`: T1 commits writes; T2 (read-only) reads snapshot 101/102 and commits.
- `test_comprehensive.txt`: All transactions commit except none aborted; final dump reflects sequence (x1=111, x2=122, x3=233, x4=344, x6=166 with proper placement).
