"""
Transaction - models a transaction lifecycle and state.
"""

from enum import Enum
from typing import Dict, Set


class TransactionStatus(Enum):
    """Transaction status enum."""

    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    WAITING = "WAITING"


class Transaction:
    """
    Transaction tracks one transaction's lifecycle and operations.

    Attributes:
        id: Transaction id (e.g., "T1").
        start_timestamp: Logical time when it begins.
        commit_timestamp: Logical time when it commits.
        status: Current status.
        read_set: Variables read.
        write_set: Private workspace writes.
        sites_written_to: Sites that will be written on commit.
        is_read_only: Whether it is read-only.
        waiting_for_variable: Variable it is blocked on.
        waiting_operation: Deferred operation tuple to retry.
        deferred_operations: FIFO queue for additional operations issued while waiting.
        site_failed_after_write: Flag set if a written site failed before commit.
    """

    def __init__(self, transaction_id: str, start_timestamp: int, is_read_only: bool = False):
        """
        Purpose: initialize transaction state.
        Author: Xi Wang
        Args: transaction_id, start_timestamp, is_read_only
        Returns: None
        Side effects: sets baseline state and collections.
        """
        self.id = transaction_id
        self.start_timestamp = start_timestamp
        self.commit_timestamp = None
        self.status = TransactionStatus.ACTIVE
        self.read_set: Set[str] = set()
        self.write_set: Dict[str, int] = {}
        self.sites_written_to: Set[int] = set()
        self.is_read_only = is_read_only
        self.waiting_for_variable = None
        self.waiting_operation = None
        self.deferred_operations = []
        self.site_failed_after_write = False

    def read(self, variable: str):
        """
        Purpose: record a read variable.
        Author: Sihang Zhao
        Args: variable - variable id.
        Returns: None
        Side effects: adds to read_set.
        """
        self.read_set.add(variable)

    def write(self, variable: str, value: int):
        """
        Purpose: stage a write in the private workspace.
        Author: Xi Wang
        Args: variable, value
        Returns: None
        Side effects: updates write_set.
        """
        self.write_set[variable] = value

    def add_site_written(self, site_id: int):
        """
        Purpose: record a site that will be written.
        Author: Sihang Zhao
        Args: site_id
        Returns: None
        Side effects: updates sites_written_to.
        """
        self.sites_written_to.add(site_id)

    def set_waiting(self, variable: str = None, op=None):
        """
        Purpose: mark transaction as waiting and remember deferred op.
        Author: Xi Wang
        Args: variable (optional) it waits for; op (optional) tuple describing deferred operation.
        Returns: None
        Side effects: status -> WAITING, sets waiting_for_variable/operation.
        """
        self.status = TransactionStatus.WAITING
        self.waiting_for_variable = variable
        if op is not None:
            self.waiting_operation = op

    def queue_operation(self, op):
        """
        Purpose: enqueue an operation issued while waiting.
        Author: Sihang Zhao
        Args: op (tuple)
        Returns: None
        Side effects: appends to deferred_operations.
        """
        self.deferred_operations.append(op)

    def set_active(self):
        """
        Purpose: mark transaction active.
        Author: Sihang Zhao
        Args: None
        Returns: None
        Side effects: status -> ACTIVE, clears waiting_for_variable.
        """
        self.status = TransactionStatus.ACTIVE
        self.waiting_for_variable = None
        self.waiting_operation = None

    def abort(self):
        """
        Purpose: abort transaction.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: status -> ABORTED.
        """
        self.status = TransactionStatus.ABORTED

    def commit(self, commit_timestamp: int):
        """
        Purpose: commit transaction.
        Author: Sihang Zhao
        Args: commit_timestamp - logical commit time.
        Returns: None
        Side effects: sets commit_timestamp and status -> COMMITTED.
        """
        self.commit_timestamp = commit_timestamp
        self.status = TransactionStatus.COMMITTED

    def __str__(self):
        """Purpose: human-readable summary. Author: Xi Wang. Args: None. Returns: str."""
        return (
            f"Transaction({self.id}, status={self.status.value}, "
            f"start={self.start_timestamp}, commit={self.commit_timestamp})"
        )

    def __repr__(self):
        """Purpose: debug representation. Author: Sihang Zhao. Args: None. Returns: str."""
        return self.__str__()
