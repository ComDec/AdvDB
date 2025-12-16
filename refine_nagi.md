# Refinement Summary (Nagi_dev)

- Fixed site failure crash by keeping only the latest version per replica via `reset_snapshot_history`.
- Abort non-replicated writes when their sole site is down at commit to prevent lost updates.
- Excluded read-only transactions from SSI RW checks to avoid false aborts.
- Failure flagging now only marks transactions that wrote odd (single-copy) variables on a failed site.
- Retained available-copies behavior; replicated writes still broadcast to all up sites; waiting transactions are retried after recovery.

