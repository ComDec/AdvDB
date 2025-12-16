# RepCRec Simulator

Distributed replicated database simulator implementing serializable snapshot isolation (SSI), multi-version storage, and the available-copies (ROWAA) replication rules from `handDB2-4-11.pdf`.

## Requirements
- Python 3.9+ (standard library only)

## Run
- From a script: `python main.py <input_file>`
- Interactive: `python main.py` then enter commands line by line.
- ReproZip trace (from base environment): `mamba activate base && reprozip trace python main.py test_basic.txt` then `reprozip pack repcrec.rpz` to produce the `.rpz` bundle; unpack with `reprounzip directory setup repcrec.rpz run_dir` then `reprounzip directory run run_dir`.

Supported commands follow the project spec: `begin(T1)`, `beginRO(T2)`, `R(T1, x4)`, `W(T1, x2, 50)`, `end(T1)`, `fail(3)`, `recover(3)`, `dump()`, `dump(2)`, `dump(x4)`. Lines starting with `//` are comments.

Each line advances logical time by one tick. Reads print `x#: value`, commits/aborts print `T commits/aborts`, and writes report which sites were updated.

## Tests
- Quick run: `./run_all_tests.sh`
- Or individually: `python main.py test_basic.txt` (others: `test_ww_conflict.txt`, `test_rw_conflict.txt`, `test_snapshot.txt`, `test_site_failure.txt`, `test_replicated.txt`, `test_readonly.txt`, `test_comprehensive.txt`).
- To capture a reproducible run, ensure you are in the `base` environment (`mamba activate base`) with `reprozip` installed, then run tests under `reprozip trace ...` as shown above.

### ReproZip usage (full suite)
- Install tools if needed: `pip install --user reprozip reprounzip` (ensure `~/.local/bin` is on PATH).
- Trace + pack the full public suite:  
  `reprozip trace --overwrite python run_public_tests.py`  
  `reprozip pack repcrec_latest.rpz`
- Replay elsewhere (no source tree changes required):  
  `reprounzip directory setup repcrec_latest.rpz run_dir`  
  `reprounzip directory run run_dir`
- The repo already contains `repcrec_latest.rpz` built from a clean run of `run_public_tests.py`.

## Notes
- Data distribution: x1..x20; odd indexes live on a single site `1 + (i mod 10)`, even indexes on all 10 sites; initial value `10*i`.
- Writes: replicated writes are staged on the sites that were up when the write was issued and are only applied to that set if those sites remain up at commit (recovered sites stay stale until a later commit touches them).
- Recovery: non-replicated copies are readable immediately after recovery; replicated copies stay stale until a new commit refreshes them for post-recovery transactions, but transactions that started before the failure can still read their snapshot version once the site is back.
- SSI checks: first-committer-wins plus dangerous-structure detection with RW antidependency chains; transactions that wrote to a site abort if that site fails before commit.
