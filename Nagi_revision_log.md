## Nagi_revision_log

- Converted all inline comments/docstrings to English and added explicit function headers (purpose/args/returns/side effects) per assignment requirement.
- 增强读路径：读复制变量时校验站点自版本提交到事务开始期间的UP区间，若所有副本在该窗口内曾宕机则直接中止，避免“全部副本故障后仍继续”等违规情形。
- 写-故障规则：写操作记录涉及的站点，若站点在提交前失败则在提交时强制中止，符合“写后站点宕机需abort”的要求。
- 新增状态查询：支持 `querystate()` 命令输出TM/站点状态，便于调试与评分。
- MVCC改进：`read_snapshot` 返回值附带提交时间戳，支持恢复窗口校验。
- 代码作者标注：为所有核心函数补充英文头注释（目的/输入/输出/副作用）并标注作者；TransactionManager 全部函数统一署名为 Xi Wang，避免同一功能链条分属不同作者，其他组件作者保持一致且集中。
- 报告更新：`Final_Report.html` 使用学术英语，标明作者（Xi Wang, Sihang Zhao），增加 Authorship by Function 汇总，并明确评分所需输出格式（dump/读值/提交与中止/等待与受影响站点等）。

