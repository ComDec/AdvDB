"""
VariableCopy - MVCC-enabled variable replica.
"""

from typing import List, Tuple


class VariableCopy:
    """
    VariableCopy - stores one replica of a variable with MVCC support.

    Attributes:
        variable_id: Variable identifier (e.g., "x1").
        value: Latest committed value (also used by dump()).
        version_history: List of (commit_timestamp, value) tuples.
        is_replicated: Whether this variable is replicated (even indexes).
        is_readable: Readable flag (stale flag for recovery).
    """

    def __init__(self, variable_id: str, initial_value: int, is_replicated: bool):
        """
        Purpose: initialize a variable replica.
        Author: Sihang Zhao
        Args: variable_id, initial_value, is_replicated
        Returns: None
        Side effects: initializes MVCC history and readability.
        """
        self.variable_id = variable_id
        self.value = initial_value  # 当前值，用于dump()操作
        self.version_history: List[Tuple[int, int]] = [(0, initial_value)]  # MVCC版本历史
        self.is_replicated = is_replicated
        self.is_readable = True  # 默认为可读

    def write(self, commit_timestamp: int, new_value: int):
        """
        Purpose: append a committed version and mark readable.
        Author: Xi Wang
        Args:
            commit_timestamp: Commit timestamp assigned by TM.
            new_value: Value to store.
        Returns: None
        Side effects: Updates current value, version_history, sets is_readable=True.
        """
        self.value = new_value
        self.version_history.append((commit_timestamp, new_value))
        # 写入后，该副本变为可读（恢复算法的关键）
        self.is_readable = True

    def read_snapshot(self, snapshot_timestamp: int) -> Tuple[int, int]:
        """
        Purpose: fetch the latest committed version before a snapshot timestamp.
        Author: Sihang Zhao
        Args:
            snapshot_timestamp: Usually the transaction start timestamp.
        Returns:
            (value, commit_ts): Latest value and its commit ts < snapshot_timestamp.
        Side effects: None.
        """
        snapshot_value = self.version_history[0][1]  # 初始值
        snapshot_commit_ts = self.version_history[0][0]

        for commit_ts, value in self.version_history:
            if commit_ts < snapshot_timestamp:
                snapshot_value = value
                snapshot_commit_ts = commit_ts
            else:
                break  # 已经找到晚于快照时间的版本，停止搜索

        return snapshot_value, snapshot_commit_ts

    def set_stale(self):
        """Purpose: mark replica unreadable after recovery. Author: Xi Wang. Args: None. Returns: None. Side effects: is_readable=False."""
        self.is_readable = False

    def set_readable(self):
        """Purpose: mark replica readable. Author: Sihang Zhao. Args: None. Returns: None. Side effects: is_readable=True."""
        self.is_readable = True

    def __str__(self):
        """
        Purpose: human-readable summary.
        Author: Xi Wang
        Args: None
        Returns: str - string representation of variable copy
        Side effects: None
        """
        return (
            f"VariableCopy({self.variable_id}={self.value}, "
            f"replicated={self.is_replicated}, readable={self.is_readable})"
        )

    def __repr__(self):
        """
        Purpose: debug representation.
        Author: Sihang Zhao
        Args: None
        Returns: str - debug string representation
        Side effects: None
        """
        return self.__str__()
