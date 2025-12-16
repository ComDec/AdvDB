# Revision Report

Xi Wang, Sihang Zhao

## Overview
Our changes focus on:
1. Site failure handling: Clear MVCC history on site failure, keep only latest value
2. Non-replicated variable protection: Abort if sole site is down at commit
3. Read-only transaction exclusion: Skip read-only transactions in SSI RW checks

Now our code can pass all the tests (49/49).
---

## File-Level Change Summary

### Commit 10c1b05 (Align RepCRec engine with ROWAA and SSI requirements)
- `variable_copy.py`: +10 lines (new method)
- `data_site.py`: +2 lines (call new method)
- `transaction_manager.py`: +3 lines (exclude read-only, check non-replicated sites)

### Commit 14c06df (fixed site failure)
- `transaction_manager.py`: +7 lines (non-replicated site check at commit)

**Total**: ~22 lines of core logic changes across 3 files

---

## Detailed Changes

### 1. variable_copy.py

#### New Method: `reset_snapshot_history()`

**Location**: Lines 79-90

**Change**:
```python
def reset_snapshot_history(self):
    """
    Purpose: drop historical versions on site failure while keeping latest value.
    Author: Sihang Zhao
    Args: None
    Returns: None
    Side effects: trims version_history to the newest committed version.
    """
    if not self.version_history:
        return
    latest_commit_ts, latest_value = self.version_history[-1]
    self.version_history = [(latest_commit_ts, latest_value)]
```

**Rationale**: 
- Required by test44: When all sites fail and recover, replicated variables lose historical versions
- Site failure means MVCC history is lost, but latest committed value must be preserved

**Test Coverage**: `test44.txt` (all sites fail scenario)

---

### 2. data_site.py

#### `Site.fail()` Method Modification

**Location**: Lines 69-73

**Before**:
```python
def fail(self):
    """Mark site as failed."""
    self.status = SiteStatus.DOWN
```

**After**:
```python
def fail(self):
    """Mark site as failed."""
    self.status = SiteStatus.DOWN
    for variable_copy in self.variables.values():
        variable_copy.reset_snapshot_history()
```

**Change**: Added loop to call `reset_snapshot_history()` on all variable copies

**Rationale**: Clear MVCC history immediately when site fails

**Test Coverage**: `test44.txt`, `test42.txt`, `test45.txt`

---

### 3. transaction_manager.py

#### `end()` Method - Non-Replicated Site Check

**Location**: Lines 219-226 (new check added)

**Change**:
```python
# if a non-replicated variable's only site is down, commit must fail
for variable_id in transaction.write_set.keys():
    variable_index = int(variable_id[1:])
    if variable_index % 2 == 1:
        target_site_id = 1 + (variable_index % 10)
        if not self.get_site(target_site_id).is_up():
            self._abort_transaction(transaction, f"site {target_site_id} down for {variable_id}")
            return
```

**Rationale**: 
- Required by test19: Non-replicated variables have only one copy
- If that site is down at commit, the write cannot be persisted → abort

**Test Coverage**: `test19.txt` (T3 writes x3, site 4 fails, T3 must abort)

---

#### `_check_rw_conflict()` Method - Exclude Read-Only Transactions

**Location**: Lines 276-279

**Before**:
```python
def _check_rw_conflict(self, transaction: Transaction) -> bool:
    for committed_tx in self.committed_transactions:
        # only commits after T started
        if committed_tx.commit_timestamp > transaction.start_timestamp:
```

**After**:
```python
def _check_rw_conflict(self, transaction: Transaction) -> bool:
    for committed_tx in self.committed_transactions:
        # skip read-only transactions; they do not create dangerous structures
        if committed_tx.is_read_only:
            continue
        # only commits after T started
        if committed_tx.commit_timestamp > transaction.start_timestamp:
```

**Change**: Added check to skip read-only transactions

**Rationale**: 
- Read-only transactions don't write, so they cannot create RW conflicts
- Prevents false aborts (refine_nagi.md point 3)

**Test Coverage**: All read-only transaction tests (`test_readonly.txt`, `test_issue2.txt`)

---

## Change Summary

### Core Changes (Minimal Set)

1. **Site Failure History Clearing** (`variable_copy.py`, `data_site.py`)
   - New method: `reset_snapshot_history()` 
   - Called in `Site.fail()` to clear MVCC history
   - **Lines changed**: ~12 lines

2. **Non-Replicated Variable Protection** (`transaction_manager.py`)
   - Check in `end()`: abort if sole site is down at commit
   - **Lines changed**: ~7 lines

3. **Read-Only Transaction Exclusion** (`transaction_manager.py`)
   - Skip read-only transactions in `_check_rw_conflict()`
   - **Lines changed**: ~3 lines

**Total Core Changes**: ~22 lines across 3 files

### Test Validation

All 49 test cases pass, including:
- `test_issue1.txt`: Site recovery and write after recovery
- `test_issue2.txt`: Sequential transactions (read-only exclusion)
- `test19.txt`: Non-replicated variable site failure
- `test42.txt`: Wait for non-replicated variable recovery
- `test44.txt`: All sites fail scenario
- `test45.txt`: Write then site failure

---

## Git Commit History

- **10c1b05**: Align RepCRec engine with ROWAA and SSI requirements (2025-11-05)
- **14c06df**: fixed site failure (2025-12-15)

---

## Related Documents
- `test_results.log`: Test execution log
