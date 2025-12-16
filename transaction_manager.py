"""
TransactionManager - central controller (never fails).
"""

from typing import Dict, List, Optional, Set, Tuple

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
        # rw_out_edges[from] = set of transactions this transaction has RW edges to (reader -> writer)
        self.rw_out_edges: Dict[str, Set[str]] = {}
        # rw_in_edges[to] = set of transactions that have RW edges into this transaction
        self.rw_in_edges: Dict[str, Set[str]] = {}
        self.current_timestamp = 0

        # initialize 10 sites with variables
        for i in range(1, 11):
            site = Site(i)
            site.initialize_variables()
            self.sites.append(site)

    def tick(self):
        """
        Purpose: advance logical clock by one.
        Author: Sihang Zhao
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
        Author: Sihang Zhao
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
        Author: Sihang Zhao
        Args: transaction_id, variable_id (e.g., "x1")
        Returns: None
        Side effects: may block tx, abort tx, or print read value.
        """
        transaction = self.transactions.get(transaction_id)

        if not transaction or transaction.status == TransactionStatus.ABORTED:
            return

        if transaction.status == TransactionStatus.WAITING:
            transaction.queue_operation(("read", variable_id))
            print(f"{transaction_id} queued read {variable_id} while waiting")
            return

        variable_index = int(variable_id[1:])

        # Step 1: read-your-own-write
        if variable_id in transaction.write_set:
            transaction.read(variable_id)
            value = transaction.write_set[variable_id]
            print(f"{variable_id}: {value}")
            return

        # non-replicated variable
        if variable_index % 2 == 1:
            target_site_id = 1 + (variable_index % 10)
            site = self.get_site(target_site_id)

            if not site.is_up():
                transaction.set_waiting(variable_id, ("read", variable_id))
                print(f"{transaction_id} waits for {variable_id} (site {target_site_id} down)")
                return

            variable_copy = site.get_variable(variable_id)
            snapshot_value, _ = variable_copy.read_snapshot(transaction.start_timestamp)
            transaction.read(variable_id)
            print(f"{variable_id}: {snapshot_value}")
            return

        # replicated variable
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

            last_fail = self._last_failure_time(site.site_id)
            started_before_failure = last_fail is not None and transaction.start_timestamp <= last_fail
            if site.is_up() and (variable_copy.is_readable or started_before_failure):
                candidates.append((commit_ts, site.site_id, value))

        if candidates:
            commit_ts, site_id, snapshot_value = max(candidates, key=lambda c: c[0])
            transaction.read(variable_id)
            print(f"{variable_id}: {snapshot_value}")
            return

        total_sites_with_var = len([s for s in self.sites if s.has_variable(variable_id)])
        if disqualified_sites == total_sites_with_var and total_sites_with_var > 0:
            self._abort_transaction(transaction, f"no consistent copy of {variable_id}")
            return

        transaction.set_waiting(variable_id, ("read", variable_id))
        print(f"{transaction_id} waits for {variable_id} (no available copy)")

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

        if transaction.is_read_only:
            self._abort_transaction(transaction, "read-only transaction attempted a write")
            return

        if transaction.status == TransactionStatus.WAITING:
            transaction.queue_operation(("write", variable_id, value))
            print(f"{transaction_id} queued write {variable_id} while waiting")
            return

        variable_index = int(variable_id[1:])

        # non-replicated variable must wait for its unique site
        if variable_index % 2 == 1:
            target_site_id = 1 + (variable_index % 10)
            site = self.get_site(target_site_id)
            if not site.is_up():
                transaction.set_waiting(variable_id, ("write", variable_id, value))
                print(f"{transaction_id} waits to write {variable_id} (site {target_site_id} down)")
                return
            transaction.write(variable_id, value)
            transaction.record_write_targets(variable_id, {target_site_id})
            print(f"{transaction_id} stages {variable_id}={value} for site {target_site_id}")
            return

        # replicated variable: stage and note all currently up sites
        available_sites = [
            site.site_id for site in self.sites if site.is_up() and site.has_variable(variable_id)
        ]
        if not available_sites:
            transaction.set_waiting(variable_id, ("write", variable_id, value))
            print(f"{transaction_id} waits to write {variable_id} (no sites up)")
            return

        transaction.write(variable_id, value)
        transaction.record_write_targets(variable_id, set(available_sites))
        print(f"{transaction_id} stages {variable_id}={value} for sites {sorted(available_sites)}")

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
            transaction.queue_operation(("end",))
            print(f"{transaction_id} queued end while waiting")
            return

        # read-only commits immediately
        if transaction.is_read_only:
            self._commit_transaction(transaction)
            return

        # ensure odd-variable sites are available at commit time
        if not self._write_targets_available(transaction):
            self._abort_transaction(transaction, "write target unavailable")
            return

        if transaction.site_failed_after_write:
            self._abort_transaction(transaction, "site failed after write")
            return

        # WW conflict (First Committer Wins)
        if self._check_ww_conflict(transaction):
            self._abort_transaction(transaction, "WW conflict")
            return

        # RW dangerous structure (SSI)
        if self._check_dangerous_structure(transaction):
            self._abort_transaction(transaction, "SSI dangerous structure")
            return

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
                write_intersection = set(transaction.write_set.keys()) & set(
                    committed_tx.write_set.keys()
                )
                if write_intersection:
                    return True

        return False

    def _check_dangerous_structure(self, transaction: Transaction) -> bool:
        """
        Purpose: detect two consecutive RW edges (SSI dangerous structure).
        Author: Sihang Zhao
        Args: transaction
        Returns: True if conflict => abort, else False.
        Side effects: None.
        """
        incoming_committed = self._get_incoming_committed(transaction)
        outgoing_committed = {
            tx_id
            for tx_id in self.rw_out_edges.get(transaction.id, set())
            if self._is_committed(tx_id)
        }

        return bool(incoming_committed and outgoing_committed)

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

        affected_sites = {}

        for variable_id, value in transaction.write_set.items():
            variable_index = int(variable_id[1:])
            affected_sites[variable_id] = []
            target_sites = transaction.write_targets.get(variable_id, set())

            if variable_index % 2 == 1:
                if not target_sites:
                    target_sites = {1 + (variable_index % 10)}
            for site_id in sorted(target_sites):
                site = self.get_site(site_id)
                if site and site.is_up() and site.has_variable(variable_id):
                    site.write_variable(variable_id, transaction.commit_timestamp, value)
                    affected_sites[variable_id].append(site_id)

        self._register_rw_edges(transaction)
        self.committed_transactions.append(transaction)
        print(f"{transaction.id} commits")

        for var_id, sites in affected_sites.items():
            if sites:
                print(f"{transaction.id} wrote {var_id} to sites {sorted(sites)}")

        self._wakeup_waiting_transactions()

    def _register_rw_edges(self, transaction: Transaction):
        """
        Purpose: record RW edges for SSI tracking after a commit (reader -> writer).
        Author: Xi Wang
        Args: transaction
        Returns: None
        Side effects: updates rw_out_edges/rw_in_edges adjacency sets.
        """
        seen = set()
        others = list(self.transactions.values()) + self.committed_transactions
        for other in others:
            if not other or other.id == transaction.id:
                continue
            if other.id in seen:
                continue
            seen.add(other.id)
            if other.status == TransactionStatus.ABORTED:
                continue

            if other.start_timestamp is not None and other.start_timestamp >= transaction.commit_timestamp:
                continue

            if set(transaction.write_set.keys()) & other.read_set:
                self._add_rw_edge(other.id, transaction.id)

    def _add_rw_edge(self, from_tx: str, to_tx: str):
        """
        Purpose: add a RW edge from from_tx (reader) to to_tx (writer).
        Author: Xi Wang
        """
        if from_tx == to_tx:
            return
        self.rw_out_edges.setdefault(from_tx, set()).add(to_tx)
        self.rw_in_edges.setdefault(to_tx, set()).add(from_tx)

    def _get_incoming_committed(self, transaction: Transaction) -> Set[str]:
        """Return committed transactions that have RW/WW edges into this transaction."""
        incoming = set()
        for src in self.rw_in_edges.get(transaction.id, set()):
            if self._is_committed(src):
                incoming.add(src)

        for other in self.transactions.values():
            if other.id == transaction.id or other.status == TransactionStatus.ABORTED:
                continue
            if not self._is_committed(other.id):
                continue
            if other.commit_timestamp and other.commit_timestamp <= transaction.start_timestamp:
                continue
            if set(transaction.write_set.keys()) & other.read_set:
                incoming.add(other.id)

        for committed_tx in self.committed_transactions:
            if committed_tx.id == transaction.id:
                continue
            if committed_tx.status != TransactionStatus.COMMITTED:
                continue
            if set(transaction.write_set.keys()) & set(committed_tx.write_set.keys()):
                incoming.add(committed_tx.id)

        return incoming

    def _is_committed(self, tx_id: str) -> bool:
        """Check whether a transaction id refers to a committed transaction."""
        tx = self.transactions.get(tx_id)
        if tx and tx.status == TransactionStatus.COMMITTED:
            return True
        for committed_tx in self.committed_transactions:
            if committed_tx.id == tx_id and committed_tx.status == TransactionStatus.COMMITTED:
                return True
        return False

    def _remove_edges(self, tx_id: str):
        """Remove all RW edges involving a transaction (on abort)."""
        self.rw_out_edges.pop(tx_id, None)
        self.rw_in_edges.pop(tx_id, None)
        for targets in self.rw_out_edges.values():
            targets.discard(tx_id)
        for sources in self.rw_in_edges.values():
            sources.discard(tx_id)

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
        transaction.deferred_operations.clear()
        transaction.waiting_operation = None
        transaction.waiting_for_variable = None
        self._remove_edges(transaction.id)

        if reason:
            print(f"{transaction.id} aborts ({reason})")
        else:
            print(f"{transaction.id} aborts")

        self._wakeup_waiting_transactions()

    def _write_targets_available(self, transaction: Transaction) -> bool:
        """
        Purpose: ensure write targets are available (unique sites must be UP; replicated need at least one UP).
        Author: Sihang Zhao
        Args: transaction
        Returns: True if writes can proceed, else False.
        Side effects: None.
        """
        if not transaction.write_set:
            return True

        for variable_id in transaction.write_set:
            variable_index = int(variable_id[1:])
            targets = transaction.write_targets.get(variable_id, set())
            if variable_index % 2 == 1:
                target_site_id = next(iter(targets), 1 + (variable_index % 10))
                if not self.get_site(target_site_id).is_up():
                    return False
            else:
                if not targets:
                    return False
                if not any(self.get_site(site_id).is_up() for site_id in targets):
                    return False

        return True

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

    def _last_failure_time(self, site_id: int) -> Optional[int]:
        """Return timestamp of the last recorded failure for a site."""
        for sid, event, ts in reversed(self.failure_history):
            if sid == site_id and event == "down":
                return ts
        return None

    def _wakeup_waiting_transactions(self):
        """
        Purpose: wake waiting transactions; retry deferred operations in order.
        Author: Xi Wang
        """
        for tx_id, transaction in self.transactions.items():
            if transaction.status != TransactionStatus.WAITING:
                continue

            pending_ops = []
            if transaction.waiting_operation:
                pending_ops.append(transaction.waiting_operation)
            pending_ops.extend(transaction.deferred_operations)
            transaction.deferred_operations = []
            transaction.waiting_operation = None

            transaction.set_active()

            for op in pending_ops:
                if transaction.status == TransactionStatus.ABORTED:
                    break
                if transaction.status == TransactionStatus.WAITING:
                    transaction.queue_operation(op)
                    break
                self._dispatch_deferred(tx_id, op)

    def _dispatch_deferred(self, tx_id: str, op: tuple):
        """
        Purpose: rerun a deferred operation when a transaction wakes.
        Author: Sihang Zhao
        Args: tx_id, op tuple
        Returns: None
        Side effects: routes operation to read/write/end handlers.
        """
        kind = op[0]
        if kind == "read":
            self.read(tx_id, op[1])
        elif kind == "write":
            self.write(tx_id, op[1], op[2])
        elif kind == "end":
            self.end(tx_id)

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

        self.failure_history.append((site_id, "down", self.current_timestamp))

        print(f"Site {site_id} fails")

        for transaction in self.transactions.values():
            if transaction.status in [TransactionStatus.ACTIVE, TransactionStatus.WAITING]:
                if site_id in transaction.sites_written_to:
                    transaction.site_failed_after_write = True

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

        self.failure_history.append((site_id, "up", self.current_timestamp))

        print(f"Site {site_id} recovers")

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
                for var_id in transaction.read_set:
                    var_index = int(var_id[1:])
                    if var_index % 2 == 1:
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
        Author: Sihang Zhao
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

    # ==================== Cleanup and status ====================

    def cleanup_finished_transactions(self):
        """
        Purpose: remove finished (committed/aborted) transactions from active map.
        Author: Sihang Zhao
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
