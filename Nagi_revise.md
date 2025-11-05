# Nagi_revise

## 原始版本存在的主要问题
- **ROWAA 语义缺失**：`write` 指令仅更新事务私有工作区，未将写操作立即广播到所有可用站点，也未记录受影响站点，导致单副本站点宕机仍可能提交。
- **写后站点故障未触发中止**：事务对象虽包含 `sites_written_to` 字段，但没有记录写入时间；站点故障时只检查读集合，使得写入过的站点宕机不会在 `end(T)` 阶段中止。
- **站点失败后 SSI/MVCC 信息未清除**：`Site.fail()` 仅改变状态，未重置版本历史，违背“站点失败即丢失本地 SSI 信息”的约束。
- **SSI 冲突检测不足**：原实现仅做一次读写交集判断，无法识别“连续两条 RW 边”危险结构。
- **输出日志不完整**：写指令未输出受影响站点，无法满足测试要求，也不利于调试。

## 本次修复与改动
- **重写 ROWAA 写路径**：`transaction_manager.write()` 现会枚举所有可写站点、在站点不可用时让事务等待，并输出格式化的受影响站点列表。
- **记录写站点与时间戳**：新增 `Transaction.record_write_site()` 及 `site_write_times`，`end()` 在提交前调用 `_check_site_failure_for_writes()`，若写入站点在写后宕机立即中止。
- **站点失败清空本地历史**：`Site.fail()` 调用 `VariableCopy.reset_snapshot_history()`，恢复后通过 Stale Flag 算法重新标记可读性。
- **SSI 危险结构检测**：新增 `_collect_rw_incoming_sources()` 与 `_detect_dangerous_structure()`，通过追踪已提交事务的 RW 入边，识别连续两条 RW 边导致的危险结构并中止。
- **等待与唤醒增强**：`Transaction.waiting_operation` 记录待执行操作， `_wakeup_waiting_transactions()` 会按类型重放读/写，确保原子性。
- **日志与只读提交同步**：写操作和只读事务提交均记录 RW 入边，以便后续危险结构检测。

## 受影响的核心文件
- `transaction_manager.py`
- `transaction.py`
- `data_site.py`
- `variable_copy.py`

## 测试
- `./run_all_tests.sh`

## 分支信息
- 分支：`Nagi_dev`
- 已推送至远端 `origin/Nagi_dev`

