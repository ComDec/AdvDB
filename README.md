# RepCRec - 分布式复制并发控制与恢复系统

基于可串行化快照隔离（Serializable Snapshot Isolation, SSI）和可用副本（Available Copies）算法的分布式数据库系统实现。

## 项目概述

本项目实现了一个分布式复制数据库系统，具有以下核心特性：

- **多版本并发控制（MVCC）**：支持快照隔离，事务读取开始时的数据快照
- **可串行化快照隔离（SSI）**：通过检测读-写冲突防止写偏斜等异常
- **可用副本算法**：复制变量使用"读任一，写所有可用"（ROWAA）策略
- **故障恢复**：实现基于"陈旧标志"的恢复算法
- **中央事务管理器**：单一、永不失败的事务协调器

## 系统架构

### 核心组件

1. **TransactionManager (TM)**：中央控制器，管理所有事务、站点和全局状态
2. **Site**：10个数据站点，每个站点存储变量的副本
3. **Transaction**：事务对象，跟踪读集合、写集合和状态
4. **VariableCopy**：支持MVCC的变量副本，维护版本历史

### 数据分布

- **变量**：x1到x20，共20个变量
- **初始值**：变量xi的初始值为10*i
- **复制规则**：
  - 奇数索引变量（x1, x3, ..., x19）：非复制，存储在站点 1 + (i mod 10)
  - 偶数索引变量（x2, x4, ..., x20）：复制，存储在所有10个站点

## 安装和运行

### 环境要求

- Python 3.7+
- 无需额外依赖包（纯标准库实现）

### 运行方式

#### 1. 从文件运行

```bash
python main.py <input_file>
```

例如：
```bash
python main.py test_basic.txt
```

#### 2. 交互式模式

```bash
python main.py
```

然后逐行输入命令。

## ReproZip 打包（提交所需）

为了实现跨架构的可重现性，使用 ReproZip 打包项目：

### 快速开始（Linux）
```bash
# 安装 reprozip
conda install -c conda-forge reprozip reprounzip
# 或: pip install reprozip reprounzip

# 自动化打包
./pack_with_reprozip.sh test_basic.txt

# 手动打包
reprozip trace python3 main.py test_basic.txt
reprozip pack repcrec.rpz
```

### 使用 Docker（macOS/Windows）
```bash
# 构建包含 reprozip 的 Docker 镜像
docker build -t repcrec-pack .

# 在容器内运行打包
docker run -it -v $(pwd):/app repcrec-pack bash
# 容器内:
reprozip trace python3 main.py test_basic.txt
reprozip pack repcrec.rpz
```

### 解包和运行
```bash
# 目录解包
reprounzip directory setup repcrec.rpz run_dir
reprounzip directory run run_dir python3 main.py test_basic.txt

# Docker 解包
reprounzip dockerfile repcrec.rpz
docker build -t repcrec:latest .
docker run --rm repcrec:latest python3 main.py test_basic.txt
```

**详细说明请参见 `REPROZIP_SETUP.md`。**

## 支持的命令

### 事务操作

- `begin(T1)`：开始一个读写事务T1
- `beginRO(T1)`：开始一个只读事务T1
- `R(T1, x1)`：事务T1读取变量x1
- `W(T1, x1, 100)`：事务T1将变量x1写为100
- `end(T1)`：结束事务T1（提交或中止）

### 站点操作

- `fail(1)`：站点1失败
- `recover(1)`：站点1恢复

### 查询操作

- `dump()`：打印所有站点上所有变量的值
- `dump(1)`：打印站点1上的所有变量
- `dump(x1)`：打印所有站点上变量x1的值

### 注释

- 以`//`开头的行会被忽略
- 支持行内注释

## 测试用例

项目提供了多个测试用例，涵盖不同场景：

1. **test_basic.txt**：基础读写操作
2. **test_ww_conflict.txt**：写-写冲突测试
3. **test_rw_conflict.txt**：读-写冲突测试（SSI）
4. **test_site_failure.txt**：站点故障和恢复
5. **test_replicated.txt**：复制变量的可用副本算法
6. **test_snapshot.txt**：MVCC快照读取
7. **test_readonly.txt**：只读事务
8. **test_comprehensive.txt**：综合测试

运行测试：
```bash
python main.py test_basic.txt
python main.py test_ww_conflict.txt
# ... 等等
```

## 算法实现

### 1. 多版本并发控制（MVCC）

每个变量维护一个版本历史列表，存储`(commit_timestamp, value)`元组。事务读取时，系统查找在事务开始时间之前最新提交的版本。

```python
def read_snapshot(self, snapshot_timestamp: int) -> int:
    snapshot_value = self.version_history[0][1]  # 初始值
    for commit_ts, value in self.version_history:
        if commit_ts < snapshot_timestamp:
            snapshot_value = value
        else:
            break
    return snapshot_value
```

### 2. 可串行化快照隔离（SSI）验证

在事务提交时进行两层验证：

#### 验证1：WW冲突（First Committer Wins）

```python
def _check_ww_conflict(self, transaction: Transaction) -> bool:
    for committed_tx in self.committed_transactions:
        if committed_tx.commit_timestamp > transaction.start_timestamp:
            write_intersection = set(transaction.write_set.keys()) &
                                 set(committed_tx.write_set.keys())
            if write_intersection:
                return True  # 冲突
    return False
```

#### 验证2：RW冲突（检测危险结构）

```python
def _check_rw_conflict(self, transaction: Transaction) -> bool:
    for committed_tx in self.committed_transactions:
        if committed_tx.commit_timestamp > transaction.start_timestamp:
            # 检查1：committed_tx写入了T读取的内容
            if transaction.read_set & set(committed_tx.write_set.keys()):
                return True
            # 检查2：committed_tx读取了T写入的内容
            if set(transaction.write_set.keys()) & committed_tx.read_set:
                return True
    return False
```

### 3. 可用副本（Available Copies）算法

- **读操作**：非复制变量必须从唯一站点读取；复制变量从任意可用且可读的站点读取
- **写操作**：延迟写入，仅更新事务的私有工作区
- **提交时**：写入所有可用站点

### 4. 故障恢复算法（Stale Flag Algorithm）

当站点恢复时：
- **非复制变量**：立即可读（该站点是唯一副本）
- **复制变量**：标记为不可读（陈旧），直到有新的提交写入

```python
def recover(self):
    self.status = SiteStatus.UP
    for variable_id, variable_copy in self.variables.items():
        if variable_copy.is_replicated:
            variable_copy.set_stale()  # 复制变量陈旧
        else:
            variable_copy.set_readable()  # 非复制变量可读
```

## 项目结构

```
RepCRec/
├── main.py                      # 主程序入口
├── transaction_manager.py       # 事务管理器
├── transaction.py               # 事务类
├── site.py                      # 站点类
├── variable_copy.py             # 变量副本类
├── parser.py                    # 命令解析器
├── README.md                    # 项目文档
├── requirements.txt             # 依赖（空）
└── test_*.txt                   # 测试用例文件
```

## 设计权衡

### 10小时优化策略

本实现针对10小时开发时间限制进行了以下优化：

1. **放弃分布式共识**：利用"永不失败"的中央TransactionManager，避免实现2PC或Paxos
2. **放弃图论检测**：用乐观的集合交集验证代替复杂的依赖图循环检测
3. **简化恢复逻辑**：使用简单的"陈旧标志"而非复杂的分布式恢复协议

### 核心复杂点

实现时重点关注三个核心逻辑：

1. `R(T, x_i)`中的MVCC版本查找逻辑
2. `end(T)`中的WW和RW冲突检查循环
3. `is_readable`标志在`recover()`、`R()`和`end()`之间的正确流转

## 示例

### 示例1：基础读写

```
begin(T1)
W(T1, x1, 101)
R(T1, x1)
end(T1)
dump()
```

输出：
```
T1 begins
T1 writes x1: 101 (to local workspace)
T1 reads x1: 101 (from local write)
T1 commits
site 1 - x1: 101 x11: 110
site 2 - x2: 20 x4: 40 x6: 60 x8: 80 x10: 100 x12: 120 x14: 140 x16: 160 x18: 180 x20: 200
...
```

### 示例2：写-写冲突

```
begin(T1)
begin(T2)
W(T1, x1, 100)
W(T2, x1, 200)
end(T1)
end(T2)
```

输出：
```
T1 begins
T2 begins
T1 writes x1: 100 (to local workspace)
T2 writes x1: 200 (to local workspace)
T1 commits
T2 aborts (WW conflict)
```

## 参考文献

本项目基于以下算法和论文：

1. Serializable Snapshot Isolation (SSI)
2. Available Copies Algorithm (ROWAA)
3. Multi-Version Concurrency Control (MVCC)

## 作者

针对NYU高级数据库系统课程项目的实现。

## 许可证

MIT License
