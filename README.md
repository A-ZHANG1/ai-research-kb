# 🦞 ai-research-kb — 带长期记忆的每日研究简报 agent

> 每天自动追踪 **AI Agent / AI Infra / Lakehouse（Fabric · Databricks 及竞品）** 的公开博客，
> 只推**新文章**、自动摘要、并把简报写成文件（可选邮件推送）。
> 全程**只爬公开 RSS**，安全合规。

配套设计文档见私有仓库 `A-ZHANG1/fabric-kb` 的 `tech-notes/public-research-kb-on-azure.md`。

---

## 🧠 长期记忆（核心）

这正是「定时跑 + 推送」相比「按需问一下」的关键区别 —— **系统记得它看过什么**。

用一个持久化的 **SQLite 库 `kb.db`** 实现，承担三件事：

1. **去重（只推新）**：每篇文章的 URL 入库；下次运行先查 `is_seen(url)`，**已看过的跳过**，所以你每天只收到**增量**。
2. **语料归档（可检索的知识库）**：每篇的标题/正文/摘要都存下来，**随时间累积成你自己的研究语料库** —— 这就是「长期记忆」本体，可用 `query.py` 检索。
3. **运行日志**：每次运行记录时间和新增数量。

```
kb.db
├── articles(url UNIQUE, source, title, published, fetched_at, content, summary)
└── runs(ran_at, new_count)
```

> 因为状态落在磁盘上，进程重启、VM 重开都不丢；这是「定时 agent」能做到「只看新 + 长期积累」、而临时会话做不到的根本原因。

---

## 🚀 快速开始

```bash
git clone https://github.com/A-ZHANG1/ai-research-kb.git
cd ai-research-kb

python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 可选：配置摘要用的 LLM 和邮件推送
cp .env.example .env && nano .env                 # 不配也能跑（用抽取式摘要兜底）

python src/main.py                                # 跑一次：抓新文章 -> 摘要 -> 出简报
```

输出：`digests/digest-YYYY-MM-DD.md`，控制台打印新增数量和 memory 统计。

---

## 🔍 查长期记忆

```bash
python src/query.py                 # 最近 15 篇
python src/query.py agent memory    # 关键词检索整个语料库
```

---

## ⏰ 每天自动跑（cron）

```bash
chmod +x scripts/run_daily.sh
crontab -e
# 每天 07:00 跑一次，日志写到 cron.log
0 7 * * *  /home/azureuser/ai-research-kb/scripts/run_daily.sh >> /home/azureuser/ai-research-kb/cron.log 2>&1
```

放在一台**常驻的 Azure VM** 上，就能做到「你关机/睡觉也照跑、照积累、照推送」。

---

## ⚙️ 配置

| 文件 | 作用 |
|------|------|
| `config/sources.yaml` | RSS 订阅源清单（增删源在这） |
| `.env` | LLM provider + API key（摘要）、SMTP（邮件推送）。都可选 |

**摘要 provider**：`LLM_PROVIDER=anthropic`（Claude）或 `openai`；不配则用抽取式兜底。
**邮件推送**：配 `SMTP_*` + `DIGEST_TO` 即开启；不配则只写简报文件。

---

## 🧩 架构

```
config/sources.yaml ──> fetch.py (RSS + trafilatura 正文)
                             │  跳过 memory 里已见过的
                             ▼
                        summarize.py (Claude/OpenAI/兜底)
                             │
                  memory.py (SQLite 长期记忆: 去重 + 归档)
                             │
                        digest.py (生成每日 Markdown)
                             │
                        notify.py (写文件 + 可选邮件)
```

---

## ⚠️ 合规

- 只订阅**公开 RSS**；不抓付费墙内容（如 SemiAnalysis 请用其官方订阅）。
- 遵守各站 `robots.txt` 与 ToS，限速礼貌抓取。
- 仅供**个人研究/检索**，勿二次公开发布他人受版权保护的全文。
- **不要把本工具指向任何公司内部系统**（内部资料走 M365 Copilot / Graph API，见配套文档）。

---

## 🛣️ 可扩展

- 把 `summarize` 的摘要再做一层**每日总览**（让 LLM 跨所有新文章写一段「今日要点」）。
- 给 `memory` 加 **embedding + 向量检索**（升级为语义 RAG）。
- 推送渠道扩展：Teams / Slack / webhook。
