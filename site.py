"""
Site class - represents a data management site
"""

from enum import Enum
from typing import Dict

from variable_copy import VariableCopy


class SiteStatus(Enum):
    """Site status enum"""

    UP = "UP"
    DOWN = "DOWN"


class Site:
    """
    Site - passive storage representing one of 10 data sites

    Attributes:
        site_id: site index (1-10)
        status: site status (UP/DOWN)
        variables: map from variable id to VariableCopy
    """

    def __init__(self, site_id: int):
        self.site_id = site_id
        self.status = SiteStatus.UP
        self.variables: Dict[str, VariableCopy] = {}

    def initialize_variables(self):
        """
        Initialize variables on this site following the project rules:
        - x1, x3, x5, ..., x19 (odd) are non-replicated
        - x2, x4, x6, ..., x20 (even) are replicated to all sites
        - initial value of xi is 10 * i
        - non-replicated xi lives on site 1 + (i mod 10)
        """
        # add all replicated variables (even indexes)
        for i in range(2, 21, 2):
            variable_id = f"x{i}"
            initial_value = 10 * i
            self.variables[variable_id] = VariableCopy(
                variable_id, initial_value, is_replicated=True
            )

        # add non-replicated variables (odd indexes) that belong to this site
        for i in range(1, 20, 2):
            target_site = 1 + (i % 10)
            if target_site == self.site_id:
                variable_id = f"x{i}"
                initial_value = 10 * i
                self.variables[variable_id] = VariableCopy(
                    variable_id, initial_value, is_replicated=False
                )

    def fail(self):
        """Mark site as failed."""
        self.status = SiteStatus.DOWN

    def recover(self):
        """
        Recover site with the stale-flag algorithm:
        - non-replicated variables become readable immediately
        - replicated variables are stale until a new committed write arrives
        """
        self.status = SiteStatus.UP

        # set stale flags appropriately
        for variable_id, variable_copy in self.variables.items():
            if variable_copy.is_replicated:
                variable_copy.set_stale()  # replicated copy becomes stale
            else:
                variable_copy.set_readable()  # non-replicated copy is readable immediately

    def has_variable(self, variable_id: str) -> bool:
        """Check whether this site stores the given variable."""
        return variable_id in self.variables

    def get_variable(self, variable_id: str) -> VariableCopy:
        """Get the variable copy, if present."""
        return self.variables.get(variable_id)

    def write_variable(self, variable_id: str, commit_timestamp: int, value: int):
        """Write a committed value into this site's copy."""
        if variable_id in self.variables:
            self.variables[variable_id].write(commit_timestamp, value)

    def is_up(self) -> bool:
        """Check whether the site is up."""
        return self.status == SiteStatus.UP

    def dump(self) -> str:
        """Return dump string of all variables on this site."""
        result = []
        result.append(f"site {self.site_id} -")

        # sort by variable id
        sorted_vars = sorted(self.variables.keys(), key=lambda x: int(x[1:]))

        for var_id in sorted_vars:
            var_copy = self.variables[var_id]
            result.append(f" {var_id}: {var_copy.value}")

        return "".join(result)

    def __str__(self):
        return f"Site({self.site_id}, status={self.status.value}, vars={len(self.variables)})"

    def __repr__(self):
        return self.__str__()
