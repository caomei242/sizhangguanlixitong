# 草莓私帐管理系统桌面版

本地 Mac 桌面私帐工具，面向个人账户、预算、流水、手动提醒、账单识别和 Obsidian 私帐同步。第一优先级是本地可用、口径保守、数据可导出，不把个人私帐和经营账混在一起。

## 当前能力

- `月度看板`：支持日、月、季、年范围切换；收入、支出、结余只统计已确认流水，待确认金额单独展示。
- `私人账户`：维护银行卡、支付宝、微信、现金、API 余额、话费、会员账户等个人账户，余额按快照和已确认流水计算。
- `流水记录`：支持收入、支出、转账、充值、退款；可筛选、单条编辑、批量修改确认状态。
- `预算计划`：当月预算工作台按 `长期收入 / 当期收入 / 长期支出 / 当期支出 / 储蓄` 分组；类型下拉显示为 `收入 / 单独支出 / 固定支出 / 分类支出 / 储蓄`，计划金额、标签、生效方式等常用字段可在表格内编辑。
- `全年十二月`：按月份汇总全年预算、实际、待确认和结余；月份可展开查看该月预算明细。
- `充值续费`：手动维护阈值提醒和日期提醒，用于 API 余额、话费、会员、固定支出、储蓄计划等。
- `数据导入`：支持图片或剪贴板识别，识别结果先生成待确认流水或提醒草稿。
- `设置`：显示本地数据库位置、导出 JSON、配置 MiniMax Key 和 Obsidian 路径。

## 关键口径

- 已确认流水才进入正式收入、支出、结余和预算消耗。
- 待确认金额单独展示，不混入正式统计。
- 转账和充值不计入消费预算。
- 退款按支出冲减处理。
- 储蓄在视觉上独立成组，但在可支配结余里按支出处理。
- 预算项生效方式包括 `仅当前月`、`每月持续`、`指定月份范围`。
- 预算对比支持保守别名归并：名字不同但本质同一项时，会按统一口径匹配，不直接改原始流水名称。

## MiniMax 账单识别

- 设置页可填写 MiniMax API Key，Key 只保存到 macOS Keychain，不写入仓库、SQLite 导出或备份。
- 默认 API Host 为中国站：`https://api.minimaxi.com/v1`，模型默认为 `MiniMax-M2.7`。
- 数据导入页支持本地图片和剪贴板截图识别。
- 识别流程为 MiniMax OCR MCP `understand_image` → MiniMax-M2.7 结构化 → 待确认流水/提醒草稿。
- 确认导入后，流水默认状态为 `待确认`，提醒默认状态为 `停用`。

## 本地启动

```bash
PYTHONPATH=src python3 -m private_ledger.app
```

也可以直接双击仓库根目录里的 `启动草莓私帐管理系统.command`。

## 桌面直接打开

- 桌面 `.app`：`/Users/gd/Desktop/草莓私帐管理系统.app`
- 桌面 `.command`：`/Users/gd/Desktop/启动草莓私帐管理系统.command`

日常使用优先点击桌面的 `草莓私帐管理系统.app`。桌面 `.command` 保留为调试和备用入口。

## 测试

```bash
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python3 -m pytest tests -q
```

## Obsidian 同步

可用命令行入口把 Obsidian 私帐记录同步进本地数据库。同步导入的流水默认仍以确认状态区分，具体明细以本地 SQLite 为准。

```bash
PYTHONPATH=src python3 -m private_ledger.sync_obsidian --obsidian-root "<Obsidian 财务目录>" --month 2026-04
```

## 更多文档

- [架构说明](docs/architecture.md)
- [运行与排障手册](docs/runbook.md)
- [看板时间范围设计记录](docs/superpowers/specs/2026-04-23-dashboard-period-trend-design.md)
