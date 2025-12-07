# RepCRec Simulator

Distributed replicated database simulator implementing serializable snapshot isolation (SSI), multi-version storage, and the available-copies (ROWAA) replication rules from `handDB2-4-11.pdf`.

## Requirements
- Python 3.9+ (standard library only)

## Run
- From a script: `python main.py <input_file>`
- Interactive: `python main.py` then enter commands line by line.

Supported commands follow the project spec: `begin(T1)`, `beginRO(T2)`, `R(T1, x4)`, `W(T1, x2, 50)`, `end(T1)`, `fail(3)`, `recover(3)`, `dump()`, `dump(2)`, `dump(x4)`. Lines starting with `//` are comments.

Each line advances logical time by one tick. Reads print `x#: value`, commits/aborts print `T commits/aborts`, and writes report which sites were updated.

## Tests
- Quick run: `./run_all_tests.sh`
- Or individually: `python main.py test_basic.txt` (others: `test_ww_conflict.txt`, `test_rw_conflict.txt`, `test_snapshot.txt`, `test_site_failure.txt`, `test_replicated.txt`, `test_readonly.txt`, `test_comprehensive.txt`).

## Notes
- Data distribution: x1..x20; odd indexes live on a single site `1 + (i mod 10)`, even indexes on all 10 sites; initial value `10*i`.
- Recovery: non-replicated copies are readable immediately after recovery; replicated copies stay stale until a new commit refreshes them.
- SSI checks: first-committer-wins plus dangerous-structure detection with RW antidependency chains; transactions that wrote to a site abort if that site fails before commit.
