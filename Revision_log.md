# Change Log (2025-12-16)

## Key changes
- **SSI dangerous-structure detection rework:** Added `rw_out_edges/rw_in_edges`; on commit we add RW edges from every reader of newly written variables and treat historical writers of the same variable as version-order edges. A transaction aborts for a dangerous structure when it has both committed incoming and outgoing RW edges, eliminating both false positives and false negatives (fixes `test18/test21/test22/test36`).
- **Per-variable write targets:** Transactions now remember available sites per write (`write_targets`) and only persist to those sites that are still up at commit. Sites that recovered later remain stale, preventing leakage to unlocked replicas (fixes `test23/test24`).
- **Post-recovery snapshot reads:** Transactions that started before a site failure can read their snapshot from a recovered site even if the replica is marked stale; post-recovery transactions still block until refreshed (fixes `test25` and avoids spurious aborts like `test38`).
- **Edge cleanup and failure handling:** Remove RW edges when aborting; site failures no longer abort transactions that only read from the site, while writes still abort via `site_failed_after_write`.

## Benefits
- **Concurrency correctness:** Properly captures two-step RW chains and version order, avoiding mistaken aborts in RW/WW conflict scenarios.
- **Available-copies fidelity:** Writes only reach sites that were locked in when issued, matching ROWAA expectations under partial outages and recoveries.
- **Recovery consistency:** Allows pre-failure transactions to finish with their snapshots while keeping strong consistency for new transactions.
- **Robustness:** Clearing dependency edges on abort prevents ghosts; read-after-failure no longer triggers invalid aborts.

## Covered tests/scenarios
- RW/WW dangerous structures: `test18`, `test21`, `test22`, `test36`
- Availability and recovery: `test23`, `test24`, `test25`
- Post-read site failure: `test38`
- All 45 public tests pass (see `Final_Proj/run_tests.py` definitions).
