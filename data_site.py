"""
Site - data site container.
"""

from enum import Enum
from typing import Dict

from variable_copy import VariableCopy


class SiteStatus(Enum):
    """Site status enum."""

    UP = "UP"
    DOWN = "DOWN"


class Site:
    """
    Site - passive storage node, one of 10 data sites.

    Attributes:
        site_id: Site id (1-10).
        status: SiteStatus.UP/DOWN.
        variables: Map variable_id -> VariableCopy.
    """

    def __init__(self, site_id: int):
        """
        Purpose: construct a site with empty variable map.
        Author: Xi Wang
        Args: site_id
        Returns: None
        Side effects: initializes status and storage.
        """
        self.site_id = site_id
        self.status = SiteStatus.UP
        self.variables: Dict[str, VariableCopy] = {}

    def initialize_variables(self):
        """
        Purpose: initialize variables on this site.
        Author: Sihang Zhao
        Rules:
        - Odd indexes non-replicated; placed at site 1 + (i mod 10).
        - Even indexes replicated on all sites.
        - Initial value = 10 * i.
        Args/Returns: None
        Side effects: populates self.variables.
        """
        # 添加所有复制变量（偶数索引）
        for i in range(2, 21, 2):
            variable_id = f"x{i}"
            initial_value = 10 * i
            self.variables[variable_id] = VariableCopy(
                variable_id, initial_value, is_replicated=True
            )

        # 添加属于此站点的非复制变量（奇数索引）
        for i in range(1, 20, 2):
            target_site = 1 + (i % 10)
            if target_site == self.site_id:
                variable_id = f"x{i}"
                initial_value = 10 * i
                self.variables[variable_id] = VariableCopy(
                    variable_id, initial_value, is_replicated=False
                )

    def fail(self):
        """Purpose: mark site down. Author: Xi Wang. Args: None. Returns: None. Side effects: status->DOWN."""
        self.status = SiteStatus.DOWN
        for variable_copy in self.variables.values():
            variable_copy.reset_snapshot_history()

    def recover(self):
        """
        Purpose: recover site and apply stale-flag algorithm.
        Author: Xi Wang
        Behavior:
        - Non-replicated variables become readable immediately.
        - Replicated variables become stale (unreadable) until a new committed write.
        Args/Returns: None
        Side effects: status->UP, updates readability flags.
        """
        self.status = SiteStatus.UP

        # 设置陈旧标志
        for variable_id, variable_copy in self.variables.items():
            if variable_copy.is_replicated:
                variable_copy.set_stale()  # 复制变量标记为陈旧
            else:
                variable_copy.set_readable()  # 非复制变量立即可读

    def has_variable(self, variable_id: str) -> bool:
        """Purpose: check if site holds variable. Author: Xi Wang. Args: variable_id. Returns: bool. Side effects: None."""
        return variable_id in self.variables

    def get_variable(self, variable_id: str) -> VariableCopy:
        """Purpose: get variable copy. Author: Sihang Zhao. Args: variable_id. Returns: VariableCopy or None. Side effects: None."""
        return self.variables.get(variable_id)

    def write_variable(self, variable_id: str, commit_timestamp: int, value: int):
        """
        Purpose: write committed value to local copy.
        Author: Xi Wang
        Args: variable_id, commit_timestamp, value
        Returns: None
        Side effects: updates replica if present.
        """
        if variable_id in self.variables:
            self.variables[variable_id].write(commit_timestamp, value)

    def is_up(self) -> bool:
        """Purpose: check if site is UP. Author: Sihang Zhao. Returns: bool. Side effects: None."""
        return self.status == SiteStatus.UP

    def dump(self) -> str:
        """
        Purpose: return dump string of variables sorted by id.
        Author: Xi Wang
        Args/Returns: None / str
        Side effects: None.
        """
        result = []
        result.append(f"site {self.site_id} -")

        # 按变量名排序
        sorted_vars = sorted(self.variables.keys(), key=lambda x: int(x[1:]))

        for var_id in sorted_vars:
            var_copy = self.variables[var_id]
            result.append(f" {var_id}: {var_copy.value}")

        return "".join(result)

    def __str__(self):
        """Purpose: readable site summary. Author: Sihang Zhao. Args: None. Returns: str."""
        return f"Site({self.site_id}, status={self.status.value}, vars={len(self.variables)})"

    def __repr__(self):
        """Purpose: debug representation. Author: Xi Wang. Args: None. Returns: str."""
        return self.__str__()
