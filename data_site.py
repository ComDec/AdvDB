"""
Site类 - 表示数据管理站点
"""

from enum import Enum
from typing import Dict

from variable_copy import VariableCopy


class SiteStatus(Enum):
    """站点状态枚举"""

    UP = "UP"
    DOWN = "DOWN"


class Site:
    """
    Site - 被动数据存储，代表10个数据站点之一

    Attributes:
        site_id: 站点编号 (1-10)
        status: 站点状态 (UP/DOWN)
        variables: 变量副本字典，映射变量ID到VariableCopy对象
    """

    def __init__(self, site_id: int):
        self.site_id = site_id
        self.status = SiteStatus.UP
        self.variables: Dict[str, VariableCopy] = {}

    def initialize_variables(self):
        """
        初始化站点上的变量

        根据项目规范：
        - 变量x1, x3, x5, ..., x19（奇数索引）是非复制的
        - 变量x2, x4, x6, ..., x20（偶数索引）是复制的，存在于所有站点
        - 变量xi的初始值为10*i
        - 非复制变量xi存储在站点 1 + (i mod 10)
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
        """站点失败"""
        self.status = SiteStatus.DOWN

    def recover(self):
        """
        站点恢复 - 实现"Stale Flag Algorithm"

        恢复后：
        - 非复制变量立即可读
        - 复制变量标记为不可读（陈旧），直到有新的提交写入
        """
        self.status = SiteStatus.UP

        # 设置陈旧标志
        for variable_id, variable_copy in self.variables.items():
            if variable_copy.is_replicated:
                variable_copy.set_stale()  # 复制变量标记为陈旧
            else:
                variable_copy.set_readable()  # 非复制变量立即可读

    def has_variable(self, variable_id: str) -> bool:
        """检查站点是否持有指定变量"""
        return variable_id in self.variables

    def get_variable(self, variable_id: str) -> VariableCopy:
        """获取变量副本"""
        return self.variables.get(variable_id)

    def write_variable(self, variable_id: str, commit_timestamp: int, value: int):
        """写入变量"""
        if variable_id in self.variables:
            self.variables[variable_id].write(commit_timestamp, value)

    def is_up(self) -> bool:
        """检查站点是否正常运行"""
        return self.status == SiteStatus.UP

    def dump(self) -> str:
        """返回站点上所有变量的dump字符串"""
        result = []
        result.append(f"site {self.site_id} -")

        # 按变量名排序
        sorted_vars = sorted(self.variables.keys(), key=lambda x: int(x[1:]))

        for var_id in sorted_vars:
            var_copy = self.variables[var_id]
            result.append(f" {var_id}: {var_copy.value}")

        return "".join(result)

    def __str__(self):
        return f"Site({self.site_id}, status={self.status.value}, vars={len(self.variables)})"

    def __repr__(self):
        return self.__str__()
