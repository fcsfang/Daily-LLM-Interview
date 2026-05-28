from __future__ import annotations

import os

from openai import OpenAI

from .models import DigestContext


def generate_digest(context: DigestContext) -> str:
    if _api_key():
        return _generate_with_openai(context)
    return _generate_fallback_digest(context)


def _generate_with_openai(context: DigestContext) -> str:
    config = context.config
    client_kwargs = {"api_key": _api_key()}
    base_url = _base_url()
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)
    prompt = build_prompt(context)
    response = client.chat.completions.create(
        model=_model(config),
        temperature=0.35,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是资深大模型实习面试教练。你必须用中文生成结构完整、可复习、"
                    "可口头表达的学习日报。所有问题必须有答案；来源不确定时必须写“需进一步验证”。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _api_key() -> str | None:
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")


def _base_url() -> str | None:
    if os.getenv("DEEPSEEK_API_KEY"):
        return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return os.getenv("OPENAI_BASE_URL")


def _model(config: dict) -> str:
    if os.getenv("DEEPSEEK_API_KEY"):
        return os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL") or config.get("model", "deepseek-v4-flash")
    return os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL") or config.get("model", "gpt-4.1-mini")


def build_prompt(context: DigestContext) -> str:
    profile = context.config.get("student_profile", {})
    directions = "、".join(profile.get("target_directions", []))
    source_blocks = []
    for index, source in enumerate(context.sources, start=1):
        uncertain = "，需进一步验证" if source.uncertain else ""
        source_blocks.append(
            f"[{index}] 标题：{source.title}\n链接：{source.url}\n来源：{source.source}{uncertain}\n摘录：\n{source.text[:3000]}"
        )

    return f"""
请基于下面的当天搜索资料，生成一份中文日报。

读者画像：
- 阶段：{profile.get("stage", "计算机研一")}
- 目标：{profile.get("goal", "找大模型实习")}
- 项目方向：{directions}

硬性要求：
1. 输出标题必须是：# 今日大模型实习面试日报
2. 必须严格包含这些一级结构：
   ## 1. 今日面试真题精讲
   ## 2. 今日技术博客精读
   ## 3. 今日必背问答卡片
   ## 4. 今日练习任务
3. 真题精讲筛选 3-5 道高价值问题。每道题必须包含：
   ### 问题
   ### 考察点
   ### 面试口头版回答
   ### 深入版回答
   ### 常见追问

4. 技术博客精读筛选 2-3 篇。每篇必须包含标题、链接、核心内容总结、可以转化成的面试题、对应参考答案。
5. 必背问答卡片生成 5 个，每个包含 Q、A、一句话记忆法。
6. 今日练习任务包含：1 道算法题并给出题目、思路和参考代码；1 道大模型理论题并给出参考答案；
   1 个项目任务并说明如何推进 RAG/Agent/LoRA 项目。
7. 不能只列问题，所有问题都必须有对应答案。答案要自然、具体、适合面试。
8. 不要堆链接，不要鸡汤。资料不足或来源不确定时标注“需进一步验证”。

当天日期：{context.run_date.isoformat()}

当天搜索资料：
{chr(10).join(source_blocks) if source_blocks else "没有抓取到可靠资料，请生成保底日报并标注需进一步验证。"}
""".strip()


def _generate_fallback_digest(context: DigestContext) -> str:
    date_text = context.run_date.isoformat()
    source_note = "今日未配置模型 API 或搜索资料有限，以下内容为保底学习日报，来源相关表述需进一步验证。"
    return f"""# 今日大模型实习面试日报

> 日期：{date_text}
> 说明：{source_note}

## 1. 今日面试真题精讲

### 问题 1：RAG 系统为什么经常出现“检索到了但答不好”？你会怎么排查？

### 考察点
考察 RAG 全链路理解：query 改写、召回、重排、上下文组装、生成约束、评测定位。

### 面试口头版回答
我会把它拆成“有没有找对、有没有排对、有没有喂对、有没有答对”四步。先看召回结果是否包含答案证据；如果有，再看重排是否把证据放到前面；然后检查 chunk 是否太碎或太长、上下文是否被截断；最后看 prompt 是否要求模型基于证据回答并拒答无依据内容。排查时我会做 case log，把 query、top-k 文档、最终上下文、模型答案和人工标签放在一起分析。

### 深入版回答
RAG 失败通常不是单点问题。检索侧可能因为 embedding 模型不适合领域、query 太口语化、chunk 粒度不合理导致召回不足；排序侧可能缺少 cross-encoder reranker，相关文档被排在后面；生成侧可能上下文超长、证据冲突、prompt 没有引用约束，导致模型忽略材料。工程上可以用 recall@k、MRR、faithfulness、answer correctness 分层评测，并保留 trace。优化顺序一般是先修数据和切分，再调召回和重排，最后改 prompt 与引用格式。

### 常见追问
- 追问：chunk 大小怎么选？答：按文档结构优先，通常从 300-800 tokens 起步，并保留 overlap，最终看 recall 和答案完整性。
- 追问：top-k 越大越好吗？答：不是。top-k 大会增加噪声和成本，需要配合 rerank 和上下文预算。
- 追问：如何减少幻觉？答：要求引用证据、无证据拒答，并用 faithfulness 评测抽查。



### 问题 2：LoRA 为什么能用较少参数完成微调？

### 考察点
考察参数高效微调、低秩分解、训练成本和部署合并理解。

### 面试口头版回答
LoRA 的核心想法是：大模型原始权重不动，只训练一个低秩增量矩阵。它假设下游任务需要的权重变化可以落在一个低维子空间里，所以把更新量拆成两个小矩阵 A 和 B。这样训练参数少、显存压力小，而且推理时可以把 LoRA 权重合并回原权重，几乎不增加推理结构复杂度。

### 深入版回答
对线性层权重 W，LoRA 不直接训练 W，而是学习增量 ΔW=BA，其中 A 和 B 的秩 r 远小于原矩阵维度。训练时冻结 W，只更新 A、B，并用缩放系数控制增量强度。优点是训练成本低、可为不同任务保存多个 adapter；缺点是容量受 rank 限制，数据质量差时仍会过拟合，且多 adapter 管理和合并需要工程规范。它适合指令风格适配、领域术语适配、小规模监督微调。

### 常见追问
- 追问：rank 怎么选？答：从 8、16、32 做验证，数据复杂度越高可能需要更大 rank。
- 追问：LoRA 和全参微调区别？答：全参容量更大但成本高，LoRA 更轻量，适合实习项目和多任务 adapter。
- 追问：可以只调部分层吗？答：可以，常见是 attention 的 q_proj、v_proj，也可扩展到 MLP。



### 问题 3：Agent 中 tool calling 的关键难点是什么？

### 考察点
考察 Agent 编排、工具 schema、状态管理、错误恢复和安全边界。

### 面试口头版回答
难点不只是让模型会调用工具，而是让它稳定、可控地调用。首先工具描述和参数 schema 要清楚，否则模型容易传错参数；其次要有状态管理，让模型知道当前已经做了什么；再者要处理工具失败，比如重试、降级或向用户澄清。最后还要做权限和安全控制，避免模型调用不该调用的工具。

### 深入版回答
Tool calling 包含意图判断、参数生成、工具执行、结果观察和下一步决策。工程难点在于 schema 设计、上下文压缩、循环终止、异常处理、幂等性和权限隔离。复杂 Agent 还需要 planner/executor 分离、短期记忆和任务状态机。评测上不能只看最终答案，还要看工具选择准确率、参数正确率、执行步数、失败恢复率和成本。

### 常见追问
- 追问：怎么防止无限循环？答：设置最大步数、状态检查和终止条件，让模型解释继续调用的必要性。
- 追问：工具返回很长怎么办？答：结构化摘要，只保留下一步决策需要的字段。
- 追问：如何评测 Agent？答：构造任务集，记录成功率、工具调用准确率、平均步数和失败原因。

### 项目联系
可以讲一个“论文助手 Agent”：工具包括搜索论文、读摘要、生成对比表，项目重点是 schema 设计、trace 可视化和失败重试。

### 记忆关键词
schema、状态、异常恢复、权限、评测

## 2. 今日技术博客精读

### 文章 1：RAG 系统评测方法综述（需进一步验证）
- 链接：需进一步验证
- 核心内容总结：RAG 评测应拆成检索质量、上下文质量和答案质量，而不是只看最终回答。常见指标包括 recall@k、MRR、faithfulness、answer relevance。
- 对面试有什么用：能把“我做过 RAG”讲成“我知道怎么定位和量化 RAG 问题”。
- 可以转化成的面试题：如何设计一个 RAG 评测集？
- 对应参考答案：先收集真实 query 和标准答案，标注支持答案的文档片段；检索侧看 recall@k/MRR，生成侧看忠实性和正确性，并保留 bad case 做迭代。

### 文章 2：LoRA/QLoRA 微调实践（需进一步验证）
- 链接：需进一步验证
- 核心内容总结：LoRA 通过低秩 adapter 降低训练参数，QLoRA 进一步用量化降低显存，适合资源有限的学生项目。
- 对面试有什么用：能回答为什么选择参数高效微调、如何控制显存、如何验证效果。
- 可以转化成的面试题：QLoRA 相比 LoRA 多解决了什么问题？
- 对应参考答案：QLoRA 主要把基座模型量化加载，减少显存占用，同时训练 LoRA adapter；它降低训练门槛，但量化可能带来精度和训练稳定性权衡。

## 3. 今日必背问答卡片

1. Q：RAG 的核心链路是什么？
   A：query 处理、召回、重排、上下文组装、生成、引用与评测。
   一句话记忆法：先找证据，再让模型按证据说话。

2. Q：LoRA 的参数为什么少？
   A：它冻结原权重，只训练低秩增量矩阵。
   一句话记忆法：不改整张地图，只学一条修正路线。

3. Q：Agent 和普通 LLM 应用的区别是什么？
   A：Agent 会基于目标多步决策，并调用工具观察环境。
   一句话记忆法：LLM 回答，Agent 做事。

4. Q：模型评测为什么要分层？
   A：因为最终答案错可能来自检索、排序、上下文或生成，不分层就难定位。
   一句话记忆法：先定位病灶，再开药。

5. Q：部署大模型时最常见的瓶颈是什么？
   A：显存、吞吐、延迟和并发成本。
   一句话记忆法：能跑只是开始，跑得稳和便宜才是部署。

## 4. 今日练习任务

### 算法题：Top K 高频元素
- 题目：给定整数数组 nums 和整数 k，返回出现频率前 k 高的元素。
- 思路：用哈希表统计频率，再用大小为 k 的小根堆维护当前最高频元素，复杂度 O(n log k)。
- 参考代码：

```python
from collections import Counter
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    heap: list[tuple[int, int]] = []
    for num, freq in counts.items():
        heapq.heappush(heap, (freq, num))
        if len(heap) > k:
            heapq.heappop(heap)
    return [num for _, num in heap]
```

### 大模型理论题：为什么 decoder-only 模型适合生成任务？
参考答案：decoder-only 模型用因果注意力建模从左到右的 token 条件概率，训练目标和生成时逐 token 预测一致。相比 encoder-only，它天然适合续写、对话和代码生成；相比 encoder-decoder，结构更统一，规模化训练和推理缓存更直接。缺点是对双向理解任务需要通过 prompt 转换，长上下文成本也较高。

### 项目任务：给 RAG 项目加一套最小评测闭环
今天完成 20 条 query 的小评测集，每条包含问题、标准答案、支持文档片段。跑当前 RAG，记录 top-5 是否命中证据、答案是否引用证据、是否出现幻觉。把失败 case 分成召回失败、重排失败、生成失败三类，明天针对最多的一类优化。
"""
