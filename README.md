# BOSS 直聘自动化（boss GUI base v1.1）

本项目用于 BOSS 直聘网页版（招聘方视角）的候选人自动沟通与筛选。

## 已实现/完善内容

- 使用 Playwright 控制 Edge（持久化 profile：`data/edge_profile`）
- 找到并激活当前 Edge 窗口，**优先 BOSS 直聘页面窗口**
- 检查 BOSS 登录状态，未登录自动停止
- 遍历候选人列表，**筛选未回复候选人（跳过数据库已联系过的候选人）**
- 发送常用语1
- 等待对方回复/简历
- 收到简历后发送常用语2
- 提取候选人姓名/学历/学校/专业/性别
- 按 985/强211 白名单判断学历
- 按其他岗位条件（包含/排除关键词）筛选
- 符合条件自动置顶
- 所有结果写入 SQLite（`data/boss.db`）
- Tkinter 图形界面：启动、停止、修改常用语、重载配置

## 运行方式

```bash
# 使用项目自带虚拟环境（Windows）
"aut3.11（64）.venv\Scripts\python.exe" main.py
```

或安装依赖后运行：

```bash
pip install -r requirements.txt
python main.py
```

## 配置说明

编辑 `config/config.json`：

| 配置项 | 说明 |
| --- | --- |
| `boss_url` | BOSS 直聘网页版聊天/候选人列表地址 |
| `common_message_1` | 首次沟通常用语 |
| `common_message_2` | 收到简历后发送的常用语 |
| `max_candidates` | 最多处理候选人数量 |
| `wait_reply_seconds` | 等待对方回复/简历的最长秒数 |
| `skip_contacted` | 是否跳过已联系过的候选人（防止重复发送常用语），默认 `true` |
| `education_check.whitelist` | 985 / 强211 学校白名单 |
| `other_conditions.require_keywords` | 必须出现的关键词 |
| `other_conditions.exclude_keywords` | 出现即排除的关键词 |
| `selectors` | BOSS 页面 DOM 选择器，页面改版后可在此调整 |

## 常见问题

1. **Edge 启动失败，提示 profile 被占用**
   先关闭正在运行的 Edge，再重新启动程序。

2. **想直接控制已经打开的 Edge**
   用 `--remote-debugging-port=9222` 启动 Edge，并在 `config/config.json`
   中填写 `cdp_url`，例如 `http://127.0.0.1:9222`。

3. **页面选择器失效**
   BOSS 直聘前端改版后，请打开浏览器开发者工具，更新 `config/config.json`
   中的 `selectors` 字段。
