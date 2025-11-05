"""
Transaction类 - 表示单个事务的状态和生命周期
"""

from enum import Enum
from typing import Dict, Set


class TransactionStatus(Enum):
    """事务状态枚举"""

    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    WAITING = "WAITING"


class Transaction:
    """
    Transaction对象跟踪单个事务的生命周期和操作

    Attributes:
        id: 事务ID (如 "T1")
        start_timestamp: 事务开始时的时间戳
        commit_timestamp: 事务提交时的时间戳
        status: 事务当前状态
        read_set: 已读取的变量集合
        write_set: 私有工作区，存储待写入的变量和值
        sites_written_to: 已写入的站点集合
        is_read_only: 是否为只读事务
    """

    def __init__(self, transaction_id: str, start_timestamp: int, is_read_only: bool = False):
        self.id = transaction_id
        self.start_timestamp = start_timestamp
        self.commit_timestamp = None
        self.status = TransactionStatus.ACTIVE
        self.read_set: Set[str] = set()  # 例如 {"x2", "x4"}
        self.write_set: Dict[str, int] = {}  # 例如 {"x1": 5, "x6": 32}
        self.sites_written_to: Set[int] = set()  # 记录已写入的站点
        self.is_read_only = is_read_only
        self.waiting_for_variable = None  # 记录正在等待的变量

    def read(self, variable: str):
        """将变量添加到读集合"""
        self.read_set.add(variable)

    def write(self, variable: str, value: int):
        """将变量和值添加到写集合（私有工作区）"""
        self.write_set[variable] = value

    def add_site_written(self, site_id: int):
        """记录已写入的站点"""
        self.sites_written_to.add(site_id)

    def set_waiting(self, variable: str = None):
        """设置事务为等待状态"""
        self.status = TransactionStatus.WAITING
        self.waiting_for_variable = variable

    def set_active(self):
        """设置事务为活跃状态"""
        self.status = TransactionStatus.ACTIVE
        self.waiting_for_variable = None

    def abort(self):
        """中止事务"""
        self.status = TransactionStatus.ABORTED

    def commit(self, commit_timestamp: int):
        """提交事务"""
        self.commit_timestamp = commit_timestamp
        self.status = TransactionStatus.COMMITTED

    def __str__(self):
        return (
            f"Transaction({self.id}, status={self.status.value}, "
            f"start={self.start_timestamp}, commit={self.commit_timestamp})"
        )

    def __repr__(self):
        return self.__str__()
