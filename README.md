# 草莓私帐管理系统桌面版

本地 Mac 桌面私帐工具，面向个人账户、预算、流水和手动提醒管理。

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
