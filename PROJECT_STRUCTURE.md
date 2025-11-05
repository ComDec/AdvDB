# RepCRec 项目结构说明

## 文件组织

```
RepCRec/
├── 核心代码文件
│   ├── main.py                      # 主程序入口
│   ├── transaction_manager.py       # 事务管理器（核心控制器）
│   ├── transaction.py               # 事务类定义
│   ├── data_site.py                 # 站点类定义
│   ├── variable_copy.py             # 变量副本类（MVCC支持）
│   └── parser.py                    # 命令解析器
│
├── 测试文件
│   ├── test_basic.txt               # 基础读写测试
│   ├── test_ww_conflict.txt         # 写-写冲突测试
│   ├── test_rw_conflict.txt         # 读-写冲突测试（SSI）
│   ├── test_site_failure.txt        # 站点故障和恢复测试
│   ├── test_replicated.txt          # 复制变量测试
│   ├── test_snapshot.txt            # MVCC快照读取测试
│   ├── test_readonly.txt            # 只读事务测试
│   └── test_comprehensive.txt       # 综合测试
│
├── 文档
│   ├── README.md                    # 完整项目文档
│   ├── QUICKSTART.md                # 快速入门指南
│   ├── PROJECT_STRUCTURE.md         # 本文件
│   └── requirements.txt             # 依赖说明（无外部依赖）
│
└── 脚本
    └── run_all_tests.sh             # 运行所有测试的脚本
```

## 核心代码文件详解

### 1. main.py
- **作用**：程序入口，处理命令行参数和用户交互
- **主要类**：`RepCRec`
- **功能**：
  - 从文件或标准输入读取命令
  - 调用TransactionManager执行命令
  - 管理时间推进（tick）

### 2. transaction_manager.py
- **作用**：系统的大脑，中央控制器
- **主要类**：`TransactionManager`
- **核心职责**：
  - 管理所有事务和站点
  - 实现MVCC读写操作
  - 实现SSI冲突检测（WW和RW）
  - 处理站点故障和恢复
  - 维护全局逻辑时钟
- **关键方法**：
  - `begin()`, `begin_read_only()`: 开始事务
  - `read()`, `write()`: 读写操作
  - `end()`: 提交/中止决策
  - `fail()`, `recover()`: 站点故障处理
  - `_check_ww_conflict()`, `_check_rw_conflict()`: SSI验证

### 3. transaction.py
- **作用**：表示单个事务的状态
- **主要类**：`Transaction`, `TransactionStatus`
- **核心属性**：
  - `start_timestamp`: 开始时间（用于快照）
  - `read_set`: 已读变量集合（用于RW检测）
  - `write_set`: 私有工作区（延迟写入）
  - `status`: ACTIVE/WAITING/COMMITTED/ABORTED

### 4. data_site.py
- **作用**：表示一个数据站点
- **主要类**：`Site`, `SiteStatus`
- **核心功能**：
  - 存储变量副本（`variables`字典）
  - 初始化变量分布
  - 处理故障/恢复（`fail()`, `recover()`）
  - 实现"陈旧标志"算法
  - 支持dump操作

### 5. variable_copy.py
- **作用**：单个变量的副本，支持MVCC
- **主要类**：`VariableCopy`
- **核心功能**：
  - 维护版本历史（`version_history`）
  - 快照读取（`read_snapshot()`）
  - 支持陈旧标志（`is_readable`）
  - 写入新版本（`write()`）

### 6. parser.py
- **作用**：解析输入命令
- **主要类**：`Parser`
- **支持格式**：
  - 事务操作：begin, beginRO, R, W, end
  - 站点操作：fail, recover
  - 查询操作：dump, dump(site), dump(var)
  - 注释：//

## 数据流图

```
用户输入
   ↓
Parser.parse_line()
   ↓
main.py (RepCRec.execute_command)
   ↓
TransactionManager (中央控制器)
   ↓
   ├→ Transaction (读写集合)
   ├→ Site (数据存储)
   └→ VariableCopy (MVCC版本)
```

## 关键算法实现位置

### MVCC快照读取
- **位置**：`variable_copy.py` 的 `read_snapshot()` 方法
- **调用**：`transaction_manager.py` 的 `read()` 方法

### SSI冲突检测
- **位置**：`transaction_manager.py`
  - `_check_ww_conflict()`: WW冲突
  - `_check_rw_conflict()`: RW冲突
- **调用**：`end()` 方法中

### Available Copies
- **读**：`transaction_manager.py` 的 `read()` 方法
  - 非复制变量：找唯一站点
  - 复制变量：找任意可用+可读站点
- **写**：`end()` 方法中的 `_commit_transaction()`
  - 写入所有UP的站点

### 恢复算法（Stale Flag）
- **位置**：`data_site.py` 的 `recover()` 方法
- **逻辑**：
  - 非复制变量 → `is_readable = True`
  - 复制变量 → `is_readable = False`（陈旧）

## 测试文件说明

### test_basic.txt
测试基本的并发事务，验证SSI基础功能

### test_ww_conflict.txt
测试First Committer Wins规则

### test_rw_conflict.txt
测试读-写依赖检测，验证可串行化

### test_site_failure.txt
测试站点失败时的等待机制和恢复后的可用性

### test_replicated.txt
测试复制变量在多站点上的读写

### test_snapshot.txt
测试MVCC快照隔离：事务看到一致的快照

### test_readonly.txt
测试只读事务的快照读取和直接提交

### test_comprehensive.txt
综合测试：包含并发、故障、恢复等多种场景

## 扩展指南

### 添加新命令

1. 在 `parser.py` 中添加解析规则
2. 在 `transaction_manager.py` 中添加处理方法
3. 在 `main.py` 的 `execute_command()` 中添加分发

### 添加新功能

1. **修改事务行为**：编辑 `transaction.py`
2. **修改站点行为**：编辑 `data_site.py`
3. **修改MVCC逻辑**：编辑 `variable_copy.py`
4. **修改协调逻辑**：编辑 `transaction_manager.py`

### 调试建议

1. 在 `TransactionManager` 中添加日志
2. 使用 `print_status()` 方法查看系统状态
3. 在测试文件中添加频繁的 `dump()` 命令
4. 使用交互式模式逐步执行命令

## 代码复杂度估计

| 文件 | 行数 | 复杂度 | 核心算法 |
|------|------|--------|----------|
| transaction_manager.py | ~350 | 高 | SSI验证，Available Copies |
| data_site.py | ~120 | 中 | 恢复算法，变量初始化 |
| variable_copy.py | ~80 | 中 | MVCC快照读取 |
| transaction.py | ~80 | 低 | 状态管理 |
| parser.py | ~120 | 低 | 正则匹配 |
| main.py | ~140 | 低 | 命令分发 |

**总代码量**：约 900 行（含注释和文档字符串）

## 设计亮点

1. **清晰的职责分离**：每个类专注于单一职责
2. **中央控制简化**：利用单一TM避免分布式共识
3. **乐观SSI验证**：集合交集代替图检测
4. **简洁的恢复**：陈旧标志代替复杂协议
5. **完整的测试**：覆盖所有核心场景

## 性能特征

- **时间复杂度**：
  - 读操作：O(V) V=版本数
  - 写操作：O(1)
  - 提交验证：O(T·N) T=已提交事务数，N=变量数

- **空间复杂度**：
  - 每个变量：O(V) V=版本数
  - 每个事务：O(R+W) R=读集合大小，W=写集合大小

## 总结

RepCRec是一个精心设计的分布式并发控制系统教学实现。通过合理的抽象和简化，在保持核心算法正确性的同时，实现了清晰易懂的代码结构。非常适合学习和理解MVCC、SSI和分布式复制算法。
