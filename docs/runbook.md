# 草莓私帐管理系统运行与排障手册

## 本地启动

开发方式启动：

```bash
PYTHONPATH=src python3 -m private_ledger.app
```

仓库内双击启动器：

```text
启动草莓私帐管理系统.command
```

桌面入口：

```text
/Users/gd/Desktop/草莓私帐管理系统.app
/Users/gd/Desktop/启动草莓私帐管理系统.command
```

如果应用已经打开，代码修改不会热更新，需要关闭窗口后重新启动。

## 测试命令

完整回归：

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests -q
```

UI 冒烟：

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_main_window.py -q
```

单文件编译检查：

```bash
python3 -m py_compile src/private_ledger/ui/main_window.py
```

## 数据位置

默认数据库：

```text
~/Library/Application Support/草莓私帐管理系统/private-ledger.db
```

旧路径兼容：

```text
~/Library/Application Support/草莓私帐
```

如果旧路径存在，仓储初始化会优先尝试迁移到 `草莓私帐管理系统` 目录。

## JSON 导出

设置页和顶部导出入口会导出本地 JSON。导出内容来自 SQLite 和应用设置，MiniMax API Key 不会写入导出文件。

## MiniMax 配置

- 设置页填写 API Key。
- Key 保存到 macOS Keychain。
- 本地数据库、JSON 导出和开发日志都不记录 Key。
- 识别失败时先检查 Keychain 是否有 Key，再检查 API Host 和模型名。

## Obsidian 同步

同步指定月份：

```bash
PYTHONPATH=src python3 -m private_ledger.sync_obsidian --obsidian-root "<Obsidian 财务目录>" --month 2026-04
```

同步指定日期：

```bash
PYTHONPATH=src python3 -m private_ledger.sync_obsidian --obsidian-root "<Obsidian 财务目录>" --date 2026-04-30
```

同步导入的数据默认遵守确认状态口径。待确认数据不会进入正式统计。

## 常见问题

### 修改代码后界面没有变化

PySide 应用不会热更新。关闭当前桌面窗口后重新打开。

### 预算页月份选择弹出日历

预算工作台应使用 12 个月下拉。如果仍看到日历，说明运行的是旧进程，重启应用。

### 预算类型看不懂

预算工作台里的类型下拉使用当前显示名：

- `收入`：收入类预算。
- `单独支出`：单独盯的一笔项目型支出。
- `固定支出`：每个月固定会发生的支出。
- `分类支出`：按标签归类的一组零碎支出。
- `储蓄`：视觉上单独展示，但统计可支配结余时仍按支出处理。

### 流水状态改完没有进入统计

确认该流水状态是否为 `已确认`。预算和看板正式口径只统计已确认流水；待确认金额会单独展示。

### 名字不同但系统把它们算成同一项

这是预算别名归并在生效。系统会保守地把少量确认过的同类名称合并统计，例如：

- `公积金收入` -> `房租补贴`
- `替尔泊肽` -> `提尔`
- `佛山税务`、`税务` -> `税务相关`
- 收入侧 `其他` -> `其他收入`

这只影响预算对比和汇总显示，不会改原始流水名称。

### 流水批量状态没有生效

先在流水表第一列勾选目标流水，再选择批量状态并点击应用。操作后页面会刷新。

### 看板某些日期趋势线为零

已确认收入、支出、结余线只展示已确认流水。待确认金额用单独的待确认线展示，不代表正式收支。

## 开发日志要求

每次完成本项目开发、测试、文档或资源调整后，更新：

```text
/Users/gd/Library/Mobile Documents/iCloud~md~obsidian/Documents/项目管理/草莓私帐管理系统--个人/开发/YYYY-MM-DD.md
```

日志只记录开发进展、测试结果和处理口径，不记录真实流水、账户余额、API Key 或其它敏感信息。
