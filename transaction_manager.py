"""
TransactionManager - central controller (never fails).
"""

from typing import Dict, List, Optional, Tuple

from data_site import Site, SiteStatus
from transaction import Transaction, TransactionStatus
from variable_copy import VariableCopy


class TransactionManager:
    """
    TransactionManager - singleton orchestrator; manages transactions, sites, and global time.

    Attributes:
        sites: List[Site] (10 sites).
        transactions: Active transaction map id -> Transaction.
        committed_transactions: Committed transactions for SSI validation.
        aborted_transactions: Aborted transactions list.
        failure_history: List of (site_id, event, ts) for up/down events.
        current_timestamp: Global logical clock.
    """

    def __init__(self):
        """
        Purpose: initialize transaction manager, sites, and clocks.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: constructs sites and resets state.
        """
        self.sites: List[Site] = []
        self.transactions: Dict[str, Transaction] = {}
        self.committed_transactions: List[Transaction] = []
        self.aborted_transactions: List[Transaction] = []
        # (site_id, event, timestamp), event in {"up","down"}
        self.failure_history: List[Tuple[int, str, int]] = []
        self.current_timestamp = 0

        # initialize 10 sites with variables
        for i in range(1, 11):
            site = Site(i)
            site.initialize_variables()
            self.sites.append(site)

    def tick(self):
        """
        Purpose: advance logical clock by one.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: increments current_timestamp.
        """
        self.current_timestamp += 1

    def get_site(self, site_id: int) -> Site:
        """
        Purpose: fetch site by id.
        Author: Xi Wang
        Args: site_id (1-based)
        Returns: Site instance
        Side effects: None.
        """
        return self.sites[site_id - 1]

    # ==================== Transaction operations ====================

    def begin(self, transaction_id: str):
        """
        Purpose: start a new read-write transaction.
        Author: Xi Wang
        Args: transaction_id (e.g., "T1")
        Returns: None
        Side effects: adds transaction to active map, prints begin.
        """
        transaction = Transaction(transaction_id, self.current_timestamp, is_read_only=False)
        self.transactions[transaction_id] = transaction
        print(f"{transaction_id} begins")

    def begin_read_only(self, transaction_id: str):
        """
        Purpose: start a new read-only transaction.
        Author: Xi Wang
        Args: transaction_id
        Returns: None
        Side effects: adds transaction; prints begin.
        """
        transaction = Transaction(transaction_id, self.current_timestamp, is_read_only=True)
        self.transactions[transaction_id] = transaction
        print(f"{transaction_id} begins (read-only)")

    def read(self, transaction_id: str, variable_id: str):
        """
        Purpose: process R(T, xi) with MVCC + replication + failure rules.
        Author: Xi Wang
        Args: transaction_id, variable_id (e.g., "x1")
        Returns: None
        Side effects: may block tx, abort tx, or print read value.
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction or transaction.status == TransactionStatus.ABORTED:
            return

        if transaction.status == TransactionStatus.WAITING:
            return

        # Step 1: read-your-own-write
        if variable_id in transaction.write_set:
            value = transaction.write_set[variable_id]
            print(f"{transaction_id} reads {variable_id}: {value} (from local write)")
            return

        # Step 2: record read
        transaction.read(variable_id)

        # Step 3: resolve target and failures
        variable_index = int(variable_id[1:])

        if variable_index % 2 == 1:  # non-replicated
            target_site_id = 1 + (variable_index % 10)
            site = self.get_site(target_site_id)

            if not site.is_up():
                transaction.set_waiting(variable_id)
                print(f"{transaction_id} waits (site {target_site_id} is down)")
                return

            # snapshot read
            variable_copy = site.get_variable(variable_id)
            snapshot_value, _ = variable_copy.read_snapshot(transaction.start_timestamp)
            print(
                f"{transaction_id} reads {variable_id}: {snapshot_value} (from site {target_site_id})"
            )

        else:  # replicated
            # find readable replica with uptime from commit_ts to txn start
            candidates = []
            disqualified_sites = 0

            for site in self.sites:
                if not site.has_variable(variable_id):
                    continue
                variable_copy = site.get_variable(variable_id)
                value, commit_ts = variable_copy.read_snapshot(transaction.start_timestamp)

                # site must be UP for [commit_ts, txn_start)
                if not self._site_up_during(site.site_id, commit_ts, transaction.start_timestamp):
                    disqualified_sites += 1
                    continue

                if site.is_up() and variable_copy and variable_copy.is_readable:
                    candidates.append((site, value))

            if candidates:
                target_site, snapshot_value = candidates[0]
                print(
                    f"{transaction_id} reads {variable_id}: {snapshot_value} (from site {target_site.site_id})"
                )
                return

            # all replicas disqualified by downtime -> abort
            total_sites_with_var = len([s for s in self.sites if s.has_variable(variable_id)])
            if disqualified_sites == total_sites_with_var and total_sites_with_var > 0:
                self._abort_transaction(transaction, f"{variable_id} lost before T started")
                return

            # otherwise wait (e.g., just recovered but stale)
            transaction.set_waiting(variable_id)
            print(f"{transaction_id} waits (no available copy of {variable_id})")

    def write(self, transaction_id: str, variable_id: str, value: int):
        """
        Purpose: handle W(T, xi, v) as deferred write to workspace.
        Author: Xi Wang
        Args: transaction_id, variable_id, value
        Returns: None
        Side effects: updates tx workspace, records target sites, prints write.
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction or transaction.status == TransactionStatus.ABORTED:
            return

        if transaction.status == TransactionStatus.WAITING:
            return

        # staging only
        transaction.write(variable_id, value)
        # track target sites for this write (used to detect single-site failures)
        target_sites = self._target_sites_for_write(variable_id)
        for site_id in target_sites:
            transaction.add_site_written(site_id)
        print(f"{transaction_id} writes {variable_id}: {value} (to local workspace)")

    def end(self, transaction_id: str):
        """
        Purpose: finalize a transaction (commit or abort) with SSI and failure checks.
        Author: Xi Wang
        Args: transaction_id
        Returns: None
        Side effects: may abort/commit, print events, wake waiting tx.
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction:
            return

        if transaction.status == TransactionStatus.ABORTED:
            print(f"{transaction_id} aborts (already aborted)")
            return

        if transaction.status == TransactionStatus.WAITING:
            # a waiting transaction cannot commit; abort immediately
            self._abort_transaction(transaction, "cannot commit while waiting")
            return

        # if a non-replicated variable's only site is down, commit must fail
        for variable_id in transaction.write_set.keys():
            variable_index = int(variable_id[1:])
            if variable_index % 2 == 1:
                target_site_id = 1 + (variable_index % 10)
                if not self.get_site(target_site_id).is_up():
                    self._abort_transaction(transaction, f"site {target_site_id} down for {variable_id}")
                    return

        # read-only commits immediately
        if transaction.is_read_only:
            self._commit_transaction(transaction)
            return

        # WW conflict (First Committer Wins)
        if self._check_ww_conflict(transaction):
            self._abort_transaction(transaction, "WW conflict")
            return

        # RW conflict (SSI)
        if self._check_rw_conflict(transaction):
            self._abort_transaction(transaction, "RW conflict (SSI)")
            return

        # all checks passed, commit transaction
        self._commit_transaction(transaction)

    # ==================== SSI validation ====================

    def _check_ww_conflict(self, transaction: Transaction) -> bool:
        """
        Purpose: detect WW conflict (First Committer Wins).
        Author: Xi Wang
        Args: transaction
        Returns: True if conflict => should abort, else False.
        Side effects: None.
        """
        for committed_tx in self.committed_transactions:
        # only commits after T started
            if committed_tx.commit_timestamp > transaction.start_timestamp:
                # intersect write sets
                write_intersection = set(transaction.write_set.keys()) & set(
                    committed_tx.write_set.keys()
                )
                if write_intersection:
                    return True  # found WW conflict

        return False  # no conflict

    def _check_rw_conflict(self, transaction: Transaction) -> bool:
        """
        Purpose: detect RW conflicts for SSI (dangerous structure).
        Author: Xi Wang
        Args: transaction
        Returns: True if conflict => abort, else False.
        Side effects: None.
        """
        for committed_tx in self.committed_transactions:
            # skip read-only transactions; they do not create dangerous structures
            if committed_tx.is_read_only:
                continue
            # only commits after T started
            if committed_tx.commit_timestamp > transaction.start_timestamp:
                # check 1: committed_tx wrote something T read
                read_write_intersection = transaction.read_set & set(committed_tx.write_set.keys())
                if read_write_intersection:
                    return True  # found RW conflict

                # check 2: committed_tx read something T wrote
                write_read_intersection = set(transaction.write_set.keys()) & committed_tx.read_set
                if write_read_intersection:
                    return True  # found RW conflict

        return False  # no conflict

    # ==================== Commit & abort ====================

    def _commit_transaction(self, transaction: Transaction):
        """
        Purpose: commit a transaction and apply writes.
        Author: Xi Wang
        Args: transaction
        Returns: None
        Side effects: sets commit ts, writes to sites, records commit, wakes waiters.
        """
        transaction.commit(self.current_timestamp)

        # apply writes to available sites
        for variable_id, value in transaction.write_set.items():
            variable_index = int(variable_id[1:])

            if variable_index % 2 == 1:  # non-replicated variable
                target_site_id = 1 + (variable_index % 10)
                site = self.get_site(target_site_id)

                if site.is_up():
                    site.write_variable(variable_id, transaction.commit_timestamp, value)

            else:  # replicated variable, write to all available sites
                for site in self.sites:
                    if site.is_up() and site.has_variable(variable_id):
                        site.write_variable(variable_id, transaction.commit_timestamp, value)

        # record commit
        self.committed_transactions.append(transaction)
        print(f"{transaction.id} commits")

        # wake waiting tx
        self._wakeup_waiting_transactions()

    def _abort_transaction(self, transaction: Transaction, reason: str = ""):
        """
        Purpose: abort transaction with optional reason.
        Author: Xi Wang
        Args: transaction, reason
        Returns: None
        Side effects: status -> ABORTED, prints, wakes waiters.
        """
        transaction.abort()
        self.aborted_transactions.append(transaction)

        if reason:
            print(f"{transaction.id} aborts ({reason})")
        else:
            print(f"{transaction.id} aborts")

        # wake waiting transactions
        self._wakeup_waiting_transactions()

    def _target_sites_for_write(self, variable_id: str) -> List[int]:
        """
        Purpose: identify sites that would be written (tracking for failure rule).
        Author: Xi Wang
        Args: variable_id
        Returns: list of site ids
        Side effects: None.
        """
        variable_index = int(variable_id[1:])
        if variable_index % 2 == 1:
            return [1 + (variable_index % 10)]
        return [site.site_id for site in self.sites if site.is_up() and site.has_variable(variable_id)]

    def _site_up_during(self, site_id: int, start_ts: int, end_ts: int) -> bool:
        """
        Purpose: check site stayed UP in (start_ts, end_ts].
        Author: Xi Wang
        Args: site_id, start_ts, end_ts
        Returns: bool
        Side effects: None.
        """
        for sid, event, ts in self.failure_history:
            if sid != site_id:
                continue
            if start_ts < ts <= end_ts and event == "down":
                return False
        return True

    def _wakeup_waiting_transactions(self):
        """
        Purpose: wake waiting transactions; retry blocked read if any.
        Author: Xi Wang
        """
        for tx_id, transaction in self.transactions.items():
            if transaction.status == TransactionStatus.WAITING:
                transaction.set_active()
                # retry the previously blocked read if any
                if transaction.waiting_for_variable:
                    self.read(tx_id, transaction.waiting_for_variable)

    # ==================== Site failure & recovery ====================

    def fail(self, site_id: int):
        """
        Purpose: handle site failure.
        Author: Xi Wang
        Args: site_id (1-10)
        Returns: None
        Side effects: marks site DOWN, logs failure, flags transactions for abort, aborts readers of odd vars on that site.
        """
        site = self.get_site(site_id)
        site.fail()

        # log failure history
        self.failure_history.append((site_id, "down", self.current_timestamp))

        print(f"Site {site_id} fails")

        # flag transactions that wrote to this site (single-copy odd variable) for abort at commit
        for transaction in self.transactions.values():
            if transaction.status in [TransactionStatus.ACTIVE, TransactionStatus.WAITING]:
                for var_id in transaction.write_set.keys():
                    var_index = int(var_id[1:])
                    # only mark transactions that wrote non-replicated variables on this site
                    if var_index % 2 == 1:
                        target_site_id = 1 + (var_index % 10)
                        if target_site_id == site_id:
                            transaction.site_failed_after_write = True
                            break

        # abort active/waiting transactions that accessed the failed site's odd variables
        self._abort_transactions_using_failed_site(site_id)

    def recover(self, site_id: int):
        """
        Purpose: handle site recovery with stale-flag algorithm.
        Author: Xi Wang
        Args: site_id (1-10)
        Returns: None
        Side effects: marks site UP, sets stale flags, logs recovery, wakes waiting tx.
        """
        site = self.get_site(site_id)
        site.recover()

        # log recovery history
        self.failure_history.append((site_id, "up", self.current_timestamp))

        print(f"Site {site_id} recovers")

        # wake waiting transactions
        self._wakeup_waiting_transactions()

    def _abort_transactions_using_failed_site(self, site_id: int):
        """
        Purpose: abort active/waiting transactions that read odd variables on failed site.
        Author: Xi Wang
        Args: site_id
        Returns: None
        Side effects: aborts affected transactions.
        """
        transactions_to_abort = []

        for tx_id, transaction in self.transactions.items():
            if transaction.status in [TransactionStatus.ACTIVE, TransactionStatus.WAITING]:
                # check whether the transaction read a non-replicated variable on this site
                for var_id in transaction.read_set:
                    var_index = int(var_id[1:])
                    if var_index % 2 == 1:  # non-replicated variable
                        target_site_id = 1 + (var_index % 10)
                        if target_site_id == site_id:
                            transactions_to_abort.append(transaction)
                            break

        for transaction in transactions_to_abort:
            self._abort_transaction(transaction, f"site {site_id} failed")

    # ==================== Dump operations ====================

    def dump(self):
        """
        Purpose: print committed values of all variables at all sites.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: writes dump output to stdout.
        """
        for site in self.sites:
            print(site.dump())

    def dump_site(self, site_id: int):
        """
        Purpose: print committed values of all variables at one site.
        Author: Xi Wang
        Args: site_id
        Returns: None
        Side effects: writes dump output to stdout.
        """
        site = self.get_site(site_id)
        print(site.dump())

    def dump_variable(self, variable_id: str):
        """
        Purpose: print committed values of a variable across sites.
        Author: Xi Wang
        Args: variable_id
        Returns: None
        Side effects: writes dump output to stdout.
        """
        results = []
        for site in self.sites:
            if site.has_variable(variable_id):
                var_copy = site.get_variable(variable_id)
                results.append(f"{variable_id}: {var_copy.value} at site {site.site_id}")

        for result in results:
            print(result)

    # ==================== Cleanup & status ====================

    def cleanup_finished_transactions(self):
        """
        Purpose: remove finished (committed/aborted) transactions from active map.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: prunes self.transactions.
        """
        finished = []
        for tx_id, transaction in self.transactions.items():
            if transaction.status in [TransactionStatus.COMMITTED, TransactionStatus.ABORTED]:
                finished.append(tx_id)

        for tx_id in finished:
            del self.transactions[tx_id]

    def print_status(self):
        """
        Purpose: print concise TM status (debug).
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: writes status to stdout.
        """
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

    def query_state(self):
        """
        Enhanced debug output including per-site dumps.
        Author: Xi Wang
        Args: None
        Returns: None
        Side effects: writes detailed state to stdout.
        """
        self.print_status()
        for site in self.sites:
            status = "UP" if site.is_up() else "DOWN"
            print(f"Site {site.site_id} [{status}] -> {site.dump()}")
