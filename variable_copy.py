"""
VariableCopy类 - 支持MVCC的变量副本
"""

from typing import List, Tuple


class VariableCopy:
    """
    VariableCopy - 存储单个变量的一个副本，支持多版本并发控制(MVCC)

    Attributes:
        variable_id: 变量ID (如 "x1")
        value: 变量的当前（最新提交的）值
        version_history: 版本历史列表，存储(commit_timestamp, value)元组
        is_replicated: 是否为复制变量（偶数索引的变量是复制的）
        is_readable: 是否可读（用于恢复算法的"陈旧标志"）
    """

    def __init__(self, variable_id: str, initial_value: int, is_replicated: bool):
        self.variable_id = variable_id
        self.value = initial_value  # 当前值，用于dump()操作
        self.version_history: List[Tuple[int, int]] = [(0, initial_value)]  # MVCC版本历史
        self.is_replicated = is_replicated
        self.is_readable = True  # 默认为可读

    def write(self, commit_timestamp: int, new_value: int):
        """
        写入新值，更新当前值和版本历史

        Args:
            commit_timestamp: 提交时间戳
            new_value: 新值
        """
        self.value = new_value
        self.version_history.append((commit_timestamp, new_value))
        # 写入后，该副本变为可读（恢复算法的关键）
        self.is_readable = True

    def read_snapshot(self, snapshot_timestamp: int) -> int:
        """
        读取快照值 - 返回在snapshot_timestamp之前最新提交的值

        Args:
            snapshot_timestamp: 快照时间戳（通常是事务的start_timestamp）

        Returns:
            在snapshot_timestamp之前的最新值
        """
        snapshot_value = self.version_history[0][1]  # 初始值

        for commit_ts, value in self.version_history:
            if commit_ts < snapshot_timestamp:
                snapshot_value = value
            else:
                break  # 已经找到晚于快照时间的版本，停止搜索

        return snapshot_value

    def set_stale(self):
        """将副本标记为陈旧（不可读）- 用于站点恢复"""
        self.is_readable = False

    def set_readable(self):
        """将副本标记为可读"""
        self.is_readable = True

    def __str__(self):
        return (
            f"VariableCopy({self.variable_id}={self.value}, "
            f"replicated={self.is_replicated}, readable={self.is_readable})"
        )

    def __repr__(self):
        return self.__str__()
