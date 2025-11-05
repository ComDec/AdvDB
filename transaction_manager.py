"""
TransactionManager类 - 中央事务管理器
"""

from typing import Dict, List, Optional, Tuple

from data_site import Site, SiteStatus
from transaction import Transaction, TransactionStatus
from variable_copy import VariableCopy


class TransactionManager:
    """
    TransactionManager - 中央控制器，永不失败的单例对象

    这是"上帝模式"控制器，管理所有事务、站点和全局状态

    Attributes:
        sites: 10个Site对象的列表
        transactions: 活跃事务字典，映射事务ID到Transaction对象
        committed_transactions: 已提交事务列表，用于SSI验证
        failure_history: 站点故障和恢复事件日志
        current_timestamp: 全局逻辑时钟
    """

    def __init__(self):
        self.sites: List[Site] = []
        self.transactions: Dict[str, Transaction] = {}
        self.committed_transactions: List[Transaction] = []
        self.aborted_transactions: List[Transaction] = []
        self.failure_history: List[Tuple[int, str, int]] = []  # (site_id, event, timestamp)
        self.current_timestamp = 0

        # 初始化10个站点
        for i in range(1, 11):
            site = Site(i)
            site.initialize_variables()
            self.sites.append(site)

    def tick(self):
        """时间推进一个单位"""
        self.current_timestamp += 1

    def get_site(self, site_id: int) -> Site:
        """获取指定ID的站点"""
        return self.sites[site_id - 1]  # site_id从1开始，列表索引从0开始

    # ==================== 事务操作 ====================

    def begin(self, transaction_id: str):
        """
        开始一个新事务

        Args:
            transaction_id: 事务ID (如 "T1")
        """
        transaction = Transaction(transaction_id, self.current_timestamp, is_read_only=False)
        self.transactions[transaction_id] = transaction
        print(f"{transaction_id} begins")

    def begin_read_only(self, transaction_id: str):
        """
        开始一个只读事务

        Args:
            transaction_id: 事务ID (如 "T1")
        """
        transaction = Transaction(transaction_id, self.current_timestamp, is_read_only=True)
        self.transactions[transaction_id] = transaction
        print(f"{transaction_id} begins (read-only)")

    def read(self, transaction_id: str, variable_id: str):
        """
        读操作 R(T, x_i)

        这是最复杂的操作之一，融合了MVCC、复制和故障处理

        Args:
            transaction_id: 事务ID
            variable_id: 变量ID (如 "x1")
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction or transaction.status == TransactionStatus.ABORTED:
            return

        if transaction.status == TransactionStatus.WAITING:
            # 事务正在等待，不处理新的读请求
            return

        # 步骤1：检查本地写入（读己之写）
        if variable_id in transaction.write_set:
            value = transaction.write_set[variable_id]
            print(f"{transaction_id} reads {variable_id}: {value} (from local write)")
            return

        # 步骤2：添加到读集合
        transaction.read(variable_id)

        # 步骤3：查找读取目标并处理故障
        variable_index = int(variable_id[1:])  # 从"x1"中提取1

        if variable_index % 2 == 1:  # 非复制变量（奇数索引）
            target_site_id = 1 + (variable_index % 10)
            site = self.get_site(target_site_id)

            if not site.is_up():
                # 站点Down，事务必须等待
                transaction.set_waiting(variable_id)
                print(f"{transaction_id} waits (site {target_site_id} is down)")
                return

            # 读取快照值
            variable_copy = site.get_variable(variable_id)
            snapshot_value = variable_copy.read_snapshot(transaction.start_timestamp)
            print(
                f"{transaction_id} reads {variable_id}: {snapshot_value} (from site {target_site_id})"
            )

        else:  # 复制变量（偶数索引）
            # 找到任何一个可用的站点
            target_site = None

            for site in self.sites:
                if site.is_up():
                    variable_copy = site.get_variable(variable_id)
                    if variable_copy and variable_copy.is_readable:
                        target_site = site
                        break

            if target_site is None:
                # 所有副本都不可用，事务等待
                transaction.set_waiting(variable_id)
                print(f"{transaction_id} waits (no available copy of {variable_id})")
                return

            # 读取快照值
            variable_copy = target_site.get_variable(variable_id)
            snapshot_value = variable_copy.read_snapshot(transaction.start_timestamp)
            print(
                f"{transaction_id} reads {variable_id}: {snapshot_value} (from site {target_site.site_id})"
            )

    def write(self, transaction_id: str, variable_id: str, value: int):
        """
        写操作 W(T, x_i, v)

        这是一个延迟写入操作，只更新事务的私有工作区

        Args:
            transaction_id: 事务ID
            variable_id: 变量ID
            value: 要写入的值
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction or transaction.status == TransactionStatus.ABORTED:
            return

        if transaction.status == TransactionStatus.WAITING:
            return

        # 只更新私有工作区，不实际写入数据库
        transaction.write(variable_id, value)
        print(f"{transaction_id} writes {variable_id}: {value} (to local workspace)")

    def end(self, transaction_id: str):
        """
        结束事务（提交或中止）

        这是所有冲突解决逻辑的中心

        Args:
            transaction_id: 事务ID
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction:
            return

        if transaction.status == TransactionStatus.ABORTED:
            print(f"{transaction_id} aborts (already aborted)")
            return

        if transaction.status == TransactionStatus.WAITING:
            # 等待中的事务尝试提交时，直接中止
            self._abort_transaction(transaction, "cannot commit while waiting")
            return

        # 只读事务直接提交（不需要验证）
        if transaction.is_read_only:
            self._commit_transaction(transaction)
            return

        # 验证1：WW冲突（First Committer Wins）
        if self._check_ww_conflict(transaction):
            self._abort_transaction(transaction, "WW conflict")
            return

        # 验证2：RW冲突（SSI验证）
        if self._check_rw_conflict(transaction):
            self._abort_transaction(transaction, "RW conflict (SSI)")
            return

        # 所有检查通过，提交事务
        self._commit_transaction(transaction)

    # ==================== SSI验证 ====================

    def _check_ww_conflict(self, transaction: Transaction) -> bool:
        """
        检查WW冲突（写-写冲突）

        First Committer Wins规则：
        如果另一个事务在T开始后提交，且写集合有交集，则T中止

        Args:
            transaction: 要检查的事务

        Returns:
            True表示有冲突（应中止），False表示无冲突
        """
        for committed_tx in self.committed_transactions:
            # 只检查在T开始后提交的事务
            if committed_tx.commit_timestamp > transaction.start_timestamp:
                # 检查写集合是否有交集
                write_intersection = set(transaction.write_set.keys()) & set(
                    committed_tx.write_set.keys()
                )
                if write_intersection:
                    return True  # 发现WW冲突

        return False  # 无冲突

    def _check_rw_conflict(self, transaction: Transaction) -> bool:
        """
        检查RW冲突（读-写冲突）

        SSI验证：检测"危险结构"或RW依赖

        Args:
            transaction: 要检查的事务

        Returns:
            True表示有冲突（应中止），False表示无冲突
        """
        for committed_tx in self.committed_transactions:
            # 只检查在T开始后提交的事务
            if committed_tx.commit_timestamp > transaction.start_timestamp:
                # 检查1：committed_tx是否写入了T读取过的内容？
                read_write_intersection = transaction.read_set & set(committed_tx.write_set.keys())
                if read_write_intersection:
                    return True  # 发现RW冲突

                # 检查2：committed_tx是否读取了T写入的内容？
                write_read_intersection = set(transaction.write_set.keys()) & committed_tx.read_set
                if write_read_intersection:
                    return True  # 发现RW冲突

        return False  # 无冲突

    # ==================== 提交和中止 ====================

    def _commit_transaction(self, transaction: Transaction):
        """
        提交事务

        Args:
            transaction: 要提交的事务
        """
        # 分配提交时间戳
        transaction.commit(self.current_timestamp)

        # 应用写入到所有可用站点
        for variable_id, value in transaction.write_set.items():
            variable_index = int(variable_id[1:])

            if variable_index % 2 == 1:  # 非复制变量
                target_site_id = 1 + (variable_index % 10)
                site = self.get_site(target_site_id)

                if site.is_up():
                    site.write_variable(variable_id, transaction.commit_timestamp, value)

            else:  # 复制变量，写入所有可用站点
                for site in self.sites:
                    if site.is_up() and site.has_variable(variable_id):
                        site.write_variable(variable_id, transaction.commit_timestamp, value)

        # 记录提交
        self.committed_transactions.append(transaction)
        print(f"{transaction.id} commits")

        # 唤醒等待中的事务
        self._wakeup_waiting_transactions()

    def _abort_transaction(self, transaction: Transaction, reason: str = ""):
        """
        中止事务

        Args:
            transaction: 要中止的事务
            reason: 中止原因
        """
        transaction.abort()
        self.aborted_transactions.append(transaction)

        if reason:
            print(f"{transaction.id} aborts ({reason})")
        else:
            print(f"{transaction.id} aborts")

        # 唤醒等待中的事务
        self._wakeup_waiting_transactions()

    def _wakeup_waiting_transactions(self):
        """
        唤醒等待中的事务

        当有事务提交或中止时，尝试重新执行等待中的事务
        """
        for tx_id, transaction in self.transactions.items():
            if transaction.status == TransactionStatus.WAITING:
                transaction.set_active()
                # 重新尝试读取之前等待的变量
                if transaction.waiting_for_variable:
                    self.read(tx_id, transaction.waiting_for_variable)

    # ==================== 站点故障与恢复 ====================

    def fail(self, site_id: int):
        """
        站点失败

        Args:
            site_id: 站点ID (1-10)
        """
        site = self.get_site(site_id)
        site.fail()

        # 记录故障历史
        self.failure_history.append((site_id, "down", self.current_timestamp))

        print(f"Site {site_id} fails")

        # 中止所有访问了该站点的活跃事务
        self._abort_transactions_using_failed_site(site_id)

    def recover(self, site_id: int):
        """
        站点恢复

        实现"Stale Flag Algorithm"

        Args:
            site_id: 站点ID (1-10)
        """
        site = self.get_site(site_id)
        site.recover()

        # 记录恢复历史
        self.failure_history.append((site_id, "up", self.current_timestamp))

        print(f"Site {site_id} recovers")

        # 唤醒等待中的事务
        self._wakeup_waiting_transactions()

    def _abort_transactions_using_failed_site(self, site_id: int):
        """
        中止所有使用了失败站点的活跃事务

        Args:
            site_id: 失败的站点ID
        """
        transactions_to_abort = []

        for tx_id, transaction in self.transactions.items():
            if transaction.status in [TransactionStatus.ACTIVE, TransactionStatus.WAITING]:
                # 检查事务是否读取了该站点上的非复制变量
                for var_id in transaction.read_set:
                    var_index = int(var_id[1:])
                    if var_index % 2 == 1:  # 非复制变量
                        target_site_id = 1 + (var_index % 10)
                        if target_site_id == site_id:
                            transactions_to_abort.append(transaction)
                            break

        for transaction in transactions_to_abort:
            self._abort_transaction(transaction, f"site {site_id} failed")

    # ==================== Dump操作 ====================

    def dump(self):
        """打印所有站点上所有变量的值"""
        for site in self.sites:
            print(site.dump())

    def dump_site(self, site_id: int):
        """打印指定站点上所有变量的值"""
        site = self.get_site(site_id)
        print(site.dump())

    def dump_variable(self, variable_id: str):
        """打印所有站点上指定变量的值"""
        results = []
        for site in self.sites:
            if site.has_variable(variable_id):
                var_copy = site.get_variable(variable_id)
                results.append(f"{variable_id}: {var_copy.value} at site {site.site_id}")

        for result in results:
            print(result)

    # ==================== 清理和状态 ====================

    def cleanup_finished_transactions(self):
        """清理已完成的事务（提交或中止的）"""
        finished = []
        for tx_id, transaction in self.transactions.items():
            if transaction.status in [TransactionStatus.COMMITTED, TransactionStatus.ABORTED]:
                finished.append(tx_id)

        for tx_id in finished:
            del self.transactions[tx_id]

    def print_status(self):
        """打印系统状态（用于调试）"""
        print(f"\n=== System Status at time {self.current_timestamp} ===")
        print(
            f"Active transactions: {len([t for t in self.transactions.values() if t.status == TransactionStatus.ACTIVE])}"
        )
        print(
            f"Waiting transactions: {len([t for t in self.transactions.values() if t.status == TransactionStatus.WAITING])}"
        )
        print(f"Committed transactions: {len(self.committed_transactions)}")
        print(f"Aborted transactions: {len(self.aborted_transactions)}")
        print(f"Sites up: {len([s for s in self.sites if s.is_up()])}/10")
        print("=" * 50)
