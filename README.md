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

没有模型 API key 时，脚本仍会生成一份结构完整的保底日报，并对来源不确定内容标注“需进一步验证”。建议配置模型 API，以获得更贴近当天搜索结果的答案。

## DeepSeek API 配置

本项目支持 DeepSeek 的 OpenAI-compatible API。GitHub Actions Secrets 中至少配置：

- `DEEPSEEK_API_KEY`

可选配置：

- `DEEPSEEK_BASE_URL`，默认 `https://api.deepseek.com`
- `DEEPSEEK_MODEL`，默认使用 `config.yaml` 中的 `deepseek-v4-flash`

如果你想使用更强的模型，可以设置：

```text
DEEPSEEK_MODEL=deepseek-v4-pro
```

本地运行示例：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek key"
export DEEPSEEK_MODEL="deepseek-v4-flash"
python run_daily.py
```

## 搜索配置

编辑 `config.yaml` 中的 `search.queries`、`trusted_domains` 和 `student_profile.target_directions` 即可调整搜索主题和日报偏向。

可选搜索 API：

- `TAVILY_API_KEY`
- `BRAVE_SEARCH_API_KEY`

如果都没有配置，系统会尝试 DuckDuckGo HTML 搜索和公开页面抽取。

## GitHub Actions 定时

仓库已包含 `.github/workflows/daily.yml`，默认每天北京时间 08:00 运行。使用 DeepSeek 时需要在 GitHub Secrets 中配置：

- `DEEPSEEK_API_KEY`
- 可选：`DEEPSEEK_MODEL`
- 可选：`DEEPSEEK_BASE_URL`

如果使用 OpenAI，则配置：

- `OPENAI_API_KEY`
- 可选：`OPENAI_MODEL`
- 可选：`OPENAI_BASE_URL`
- 可选：`TAVILY_API_KEY` 或 `BRAVE_SEARCH_API_KEY`

生成完成后可以自动推送到邮箱。需要继续在 GitHub Secrets 中配置：

- `SMTP_HOST`，例如 `smtp.gmail.com`、`smtp.qq.com`
- `SMTP_PORT`，通常是 `587`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`，建议使用邮箱服务商生成的应用专用密码或授权码
- `MAIL_TO`，收件邮箱，多个地址用英文逗号分隔
- 可选：`MAIL_FROM`，不填则使用 `SMTP_USERNAME`
- 可选：`SMTP_USE_TLS`，默认 `true`

也支持一个通用 Webhook 通道：

- `DIGEST_WEBHOOK_URL`

Webhook 会收到 JSON：

```json
{
  "title": "Daily LLM Interview Digest - 2026-05-28",
  "content": "日报 Markdown 正文"
}
```

## 本地 macOS 定时

也可以使用 launchd：

```bash
bash scripts/install_launchd.sh
```

默认每天本地时间 08:00 运行，并把日志写入 `outputs/launchd.log`。
