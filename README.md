# Daily LLM Interview Digest

每天自动搜索大模型实习相关的面经、面试题、技术博客和岗位 JD，并生成一份面向计算机研一学生的大模型实习中文学习日报。

日报会强制包含：

- 3-5 道面试真题精讲，并给出口头版回答、深入版回答、追问答案、项目联系和记忆关键词
- 2-3 篇技术博客精读，并把文章内容转化成面试题和参考答案
- 5 个必背问答卡片
- 1 道算法题、1 道大模型理论题、1 个项目推进任务

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY="你的 key"
python run_daily.py
```

生成结果会写入 `outputs/YYYY-MM-DD.md`。

没有 `OPENAI_API_KEY` 时，脚本仍会生成一份结构完整的保底日报，并对来源不确定内容标注“需进一步验证”。建议配置模型 API，以获得更贴近当天搜索结果的答案。

## 搜索配置

编辑 `config.yaml` 中的 `search.queries`、`trusted_domains` 和 `student_profile.target_directions` 即可调整搜索主题和日报偏向。

可选搜索 API：

- `TAVILY_API_KEY`
- `BRAVE_SEARCH_API_KEY`

如果都没有配置，系统会尝试 DuckDuckGo HTML 搜索和公开页面抽取。

## GitHub Actions 定时

仓库已包含 `.github/workflows/daily.yml`，默认每天北京时间 08:00 运行。需要在 GitHub Secrets 中配置：

- `OPENAI_API_KEY`
- 可选：`TAVILY_API_KEY` 或 `BRAVE_SEARCH_API_KEY`

## 本地 macOS 定时

也可以使用 launchd：

```bash
bash scripts/install_launchd.sh
```

默认每天本地时间 08:00 运行，并把日志写入 `outputs/launchd.log`。

