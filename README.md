# RepCRec Simulator

Distributed replicated database simulator implementing serializable snapshot isolation (SSI), multi-version storage, and the available-copies (ROWAA) replication rules from `handDB2-4-11.pdf`.

## Requirements
- Python 3.9+ (standard library only)

## Run
- From a script: `python main.py <input_file>`
- Interactive: `python main.py` then enter commands line by line.

Supported commands follow the project spec: `begin(T1)`, `beginRO(T2)`, `R(T1, x4)`, `W(T1, x2, 50)`, `end(T1)`, `fail(3)`, `recover(3)`, `dump()`, `dump(2)`, `dump(x4)`. Lines starting with `//` are comments.

Each line advances logical time by one tick. Reads print `x#: value`, commits/aborts print `T commits/aborts`, and writes report which sites were updated.

## Tests
- Quick run: `./run_all_tests.sh`
- Or individually: `python main.py test_basic.txt` (others: `test_ww_conflict.txt`, `test_rw_conflict.txt`, `test_snapshot.txt`, `test_site_failure.txt`, `test_replicated.txt`, `test_readonly.txt`, `test_comprehensive.txt`).

## Notes
- Data distribution: x1..x20; odd indexes live on a single site `1 + (i mod 10)`, even indexes on all 10 sites; initial value `10*i`.
- Recovery: non-replicated copies are readable immediately after recovery; replicated copies stay stale until a new commit refreshes them.
- SSI checks: first-committer-wins plus dangerous-structure detection with RW antidependency chains; transactions that wrote to a site abort if that site fails before commit.

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
