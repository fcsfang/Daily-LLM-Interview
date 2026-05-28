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
                    "你是资深大模型实习面试教练，擅长把当天搜索到的面经、技术博客和岗位 JD "
                    "转化为可复习、可背诵、可用于面试表达的中文学习日报。"
                    "你必须遵守："
                    "1. 不编造来源；没有资料支撑的问题必须标注“需进一步验证”。"
                    "2. 每个问题必须给出答案，而且答案要能直接用于口头面试。"
                    "3. 回答要包含工程视角，不只背概念。"
                    "4. 优先服务于大模型应用工程、RAG、Agent、LoRA 微调、模型评测、模型部署实习。"
                    "5. 输出必须是结构清晰的 Markdown。"
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
        return (
            os.getenv("DEEPSEEK_MODEL")
            or os.getenv("LLM_MODEL")
            or config.get("model", "deepseek-v4-flash")
        )
    return os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL") or config.get(
        "model", "gpt-4.1-mini"
    )


def build_prompt(context: DigestContext) -> str:
    profile = context.config.get("student_profile", {})
    directions = "、".join(profile.get("target_directions", []))
    source_blocks = []
    for index, source in enumerate(context.sources, start=1):
        uncertain = "，需进一步验证" if source.uncertain else ""
        source_blocks.append(
            f"[{index}] 标题：{source.title}\n链接：{source.url}\n来源：{source.source}{uncertain}\n摘录：\n{source.text[:3000]}"
        )

    source_text = (
        "\n".join(source_blocks)
        if source_blocks
        else "没有抓取到可靠资料。请生成保底日报，并在涉及来源的地方标注“需进一步验证”。"
    )
    return f"""
请基于下面的当天搜索资料，生成一份中文“大模型实习面试学习日报”。

读者画像：
- 阶段：{profile.get("stage", "计算机研一")}
- 目标：{profile.get("goal", "找大模型相关实习")}
- 重点方向：{directions or "LLM 应用、RAG、Agent、LoRA 微调、模型评测、模型部署"}
- 当前项目背景：读者正在准备大模型相关实习，希望用每日推送积累面试表达、技术理解和项目实践能力。

生成原则：
1. 不是新闻摘要，而是“面试训练包”。
2. 优先从当天资料中提炼高价值问题；资料不足时可补充经典高频题，但必须标注“需进一步验证”。
3. 不要编造公司、岗位、面试官或具体面经来源。
4. 所有问题必须有答案，答案必须适合面试口头表达。
5. 回答要体现工程实践，不能只背概念。
6. 对面经、博客、论坛内容要保持谨慎；来源不确定时标注“需进一步验证”。
7. 输出 Markdown，不要输出代码块包裹整篇日报。

输出标题必须是：
# 今日大模型实习面试日报

开头必须包含：
> 日期：{context.run_date.isoformat()}
> 今日重点：用 3 条 bullet 总结今天最值得掌握的内容。

必须严格包含以下一级结构：
## 1. 今日面试真题精讲
## 2. 今日技术博客精读
## 3. 今日必背问答卡片
## 4. 今日练习任务
## 5. 今日 60 秒背诵版

## 1. 今日面试真题精讲
请筛选 3-5 道高价值问题。每道题必须使用下面格式：

### 题目 X：问题标题
**来源依据：**
说明该问题来自哪些资料编号，例如“参考资料 [1][3]”；如果是根据资料延伸出的经典面试题，写“根据资料 [x] 延伸，需进一步验证”。

**可信度：**
高 / 中 / 低。官方文档、权威技术博客、明确岗位 JD 为高或中；个人博客、论坛、面经搬运为中或低；无明确来源为低。

**考察点：**
用 2-4 个短语说明考什么，例如：RAG 链路、召回优化、rerank、幻觉控制。

**面试口头版回答：**
给出 150-250 字答案。先给结论，再讲 2-3 个关键点，最后给一个工程例子；语言自然，像面试中可以直接说出来。

**深入理解版回答：**
给出 300-600 字解释，包含基本原理、工程流程、优点和局限、常见坑、可落地的优化或评测方法。

**常见追问与回答：**
列出 2-3 个追问，每个追问都必须有简短答案。

**项目联系：**
结合 RAG / Agent / LoRA / 模型评测 / 模型部署项目，说明这个知识点如何体现在个人项目中。尽量具体，不要泛泛地说“可以用于项目”。

**记忆关键词：**
列出 3-6 个关键词。

## 2. 今日技术博客精读
筛选 2-3 篇最值得读的资料。每篇必须包含：
- 文章标题
- 链接
- 来源依据
- 核心内容总结：3-5 条 bullet
- 对面试有什么用
- 可转化面试题：1-2 道
- 对应参考答案：每道问题都必须给出适合口头表达的答案

## 3. 今日必背问答卡片
生成 5 个 Q/A 卡片。每个卡片必须包含：
- **Q：** 问题
- **A：** 80-150 字答案，适合背诵
- **一句话记忆法：** 用一句形象的话帮助记忆
- **复习标签：** 例如 #RAG #Agent #LoRA #模型部署 #评测

## 4. 今日练习任务
必须包含 3 个任务：

### 4.1 算法题
题目来自常见面试题，优先 Hot100 高频；给出题目、思路、复杂度、Python 参考代码；代码不要太长，保证正确性和可读性。

### 4.2 大模型理论题
给出一个今日相关理论问题、参考答案、2 个可能追问。

### 4.3 项目任务
给出一个能在 1-2 小时内完成的小任务；任务必须服务于 RAG / Agent / LoRA / 模型评测 / 模型部署；明确验收标准，例如“能跑通”“能记录日志”“能在 README 中展示”。

## 5. 今日 60 秒背诵版
选今天最重要的一个问题，生成一段 60 秒口头回答。要求：开头先给结论；中间讲 2-3 个判断标准或技术点；结尾联系一个项目场景；适合直接背诵。

额外限制：
1. 不要输出空泛鼓励。
2. 不要堆砌链接。
3. 不要把同一个知识点在多个部分反复复制。
4. 如果搜索资料质量较差，必须明确说明“今日资料质量有限，以下部分为经典高频题补充，需进一步验证”。
5. 生成内容要适合沉淀到思源笔记中复习。

当天搜索资料：
{source_text}
""".strip()


def _generate_fallback_digest(context: DigestContext) -> str:
    date_text = context.run_date.isoformat()
    source_note = "今日未配置模型 API 或搜索资料有限，以下内容为保底学习日报，来源相关表述需进一步验证。"
    return f"""# 今日大模型实习面试日报

> 日期：{date_text}
> 今日重点：
> - RAG 面试要能讲清楚召回、重排、生成和评测的分层定位。
> - LoRA 面试要抓住低秩增量、冻结基座、adapter 合并这条主线。
> - Agent 面试要体现工具调用、状态管理、失败恢复和安全边界。

> 说明：{source_note}

## 1. 今日面试真题精讲

### 题目 1：RAG 系统为什么经常出现“检索到了但答不好”？你会怎么排查？

**来源依据：** 经典高频题补充，需进一步验证。

**可信度：** 低。

**考察点：** RAG 链路、召回质量、rerank、幻觉控制。

**面试口头版回答：**  
我会把问题拆成四层：有没有找对、有没有排对、有没有喂对、有没有答对。先看 top-k 结果里是否有支持答案的证据；如果有，再看 rerank 是否把关键证据排到前面；然后检查 chunk 是否太碎或太长、上下文是否被截断；最后看 prompt 是否要求模型基于证据回答并在无证据时拒答。工程上我会保存 query、召回结果、最终上下文和答案，按 case 定位问题。

**深入理解版回答：**  
RAG 失败通常不是单点问题。检索侧可能因为 embedding 模型不适合领域、query 太口语化、chunk 粒度不合理导致召回不足；排序侧可能缺少 cross-encoder reranker，使相关文档被噪声压到后面；生成侧可能因为上下文太长、证据冲突或 prompt 约束弱导致模型忽略材料。工程排查时要分层评测：检索看 recall@k、MRR，生成看 faithfulness、answer correctness，并保留 trace。优化顺序通常是先修数据和切分，再调召回与重排，最后优化 prompt、引用和拒答策略。

**常见追问与回答：**  
- 追问：top-k 越大越好吗？答：不是，top-k 大会增加噪声和成本，需要 rerank 和上下文预算配合。  
- 追问：chunk 大小怎么选？答：优先按文档结构切分，再用评测集比较不同 chunk size 的 recall 和答案完整性。  
- 追问：怎么减少幻觉？答：强制引用证据、无证据拒答，并用忠实性评测抽查。

**项目联系：**  
可以在自己的 RAG 项目中加入 trace 日志，记录 query、召回文档、rerank 分数、最终上下文、引用片段和回答，用这些 bad case 说明自己能定位并优化 RAG 系统。

**记忆关键词：** 召回、重排、chunk、faithfulness、trace。

### 题目 2：LoRA 为什么能用较少参数完成微调？

**来源依据：** 经典高频题补充，需进一步验证。

**可信度：** 低。

**考察点：** 参数高效微调、低秩分解、训练成本、adapter 部署。

**面试口头版回答：**  
LoRA 的核心是冻结大模型原始权重，只训练一个低秩的权重增量。它假设下游任务需要的参数变化可以落在较低维的子空间里，所以把更新量拆成两个小矩阵来学习。这样训练参数少、显存压力小，还能为不同任务保存不同 adapter。推理时 LoRA 权重也可以合并回原权重，部署上比较轻量。

**深入理解版回答：**  
对线性层权重 W，LoRA 不直接更新 W，而是学习增量 ΔW=BA，其中 rank r 远小于原矩阵维度。训练时冻结 W，只更新 A、B，并通过缩放系数控制增量强度。它的优点是训练成本低、适合多任务保存 adapter、易于在学生资源下做领域适配；局限是表达能力受 rank 和插入层影响，数据质量差时仍会过拟合，多个 adapter 的管理和合并也需要规范。实践中通常从 q_proj、v_proj 或 attention/MLP 关键层开始实验，用验证集比较基础模型和 LoRA 模型。

**常见追问与回答：**  
- 追问：rank 怎么选？答：从 8、16、32 做验证，复杂任务可适当增大。  
- 追问：LoRA 和全参微调区别？答：全参容量更大但成本高，LoRA 更轻量，适合资源有限和多任务场景。  
- 追问：LoRA 能解决知识注入吗？答：能做一定领域适配，但事实知识更适合结合 RAG 或高质量 SFT 数据。

**项目联系：**  
可以讲自己用 LoRA 做领域问答风格适配：准备 SFT 数据，训练 adapter，对比基础模型和微调模型在术语准确率、拒答率和人工评分上的变化。

**记忆关键词：** 低秩增量、冻结权重、adapter、rank、合并推理。

### 题目 3：Agent 中 tool calling 的关键难点是什么？

**来源依据：** 经典高频题补充，需进一步验证。

**可信度：** 低。

**考察点：** 工具 schema、状态管理、错误恢复、安全边界。

**面试口头版回答：**  
Tool calling 的难点不是让模型调用工具，而是让它稳定、可控地调用。首先工具描述和参数 schema 要清楚，否则模型容易传错参数；其次要管理状态，让模型知道已经执行了哪些步骤；再者要处理工具失败，比如重试、降级或向用户澄清。最后还要设置权限边界，避免模型调用高风险工具或泄露敏感信息。

**深入理解版回答：**  
Agent 调用工具通常包括意图判断、参数生成、工具执行、观察结果和下一步决策。工程难点在于 schema 设计、上下文压缩、循环终止、异常处理、幂等性和权限隔离。复杂任务还可能需要 planner/executor 分离、任务状态机和 trace 可视化。评测时不能只看最终答案，还要看工具选择准确率、参数正确率、平均步数、失败恢复率和成本。稳定的 Agent 往往依赖清晰工具边界和可观测日志，而不是只靠更强模型。

**常见追问与回答：**  
- 追问：怎么防止无限循环？答：设置最大步数、终止条件和状态检查。  
- 追问：工具返回很长怎么办？答：结构化摘要，只保留下一步决策需要的字段。  
- 追问：如何评测 Agent？答：构造任务集，记录成功率、工具调用准确率、平均步数和失败原因。

**项目联系：**  
可以做一个论文助手 Agent，工具包括搜索论文、读取摘要、生成对比表。面试时重点讲 schema 设计、trace 日志、失败重试和任务终止条件。

**记忆关键词：** schema、状态、重试、权限、评测。

## 2. 今日技术博客精读

### 文章 1：RAG 系统评测方法综述（需进一步验证）
- 链接：需进一步验证
- 来源依据：经典资料补充，需进一步验证
- 核心内容总结：
  - RAG 评测应拆成检索质量、上下文质量和答案质量。
  - 检索侧可看 recall@k、MRR。
  - 生成侧可看忠实性、相关性和答案正确性。
- 对面试有什么用：能把“我做过 RAG”讲成“我知道如何定位和量化 RAG 问题”。
- 可转化面试题：如何设计一个 RAG 评测集？
- 对应参考答案：先收集真实 query、标准答案和支持文档片段；检索侧看证据是否进入 top-k，生成侧看答案是否忠实引用证据，并用 bad case 反推切分、召回、重排或 prompt 问题。

### 文章 2：LoRA/QLoRA 微调实践（需进一步验证）
- 链接：需进一步验证
- 来源依据：经典资料补充，需进一步验证
- 核心内容总结：
  - LoRA 通过低秩 adapter 降低训练参数。
  - QLoRA 通过量化加载基座模型降低显存。
  - 微调效果高度依赖数据质量、rank、学习率和评测集。
- 对面试有什么用：能回答为什么选择参数高效微调、如何控制显存、如何验证效果。
- 可转化面试题：QLoRA 相比 LoRA 多解决了什么问题？
- 对应参考答案：QLoRA 主要减少基座模型加载显存，同时训练 LoRA adapter，降低资源门槛；代价是量化可能引入精度和稳定性权衡。

## 3. 今日必背问答卡片

1. **Q：** RAG 的核心链路是什么？  
   **A：** RAG 通常包括 query 处理、召回、重排、上下文组装、生成和评测。面试时不要只说“检索增强生成”，要能说明每一层可能出错，以及如何用 trace 和指标定位。  
   **一句话记忆法：** 先找证据，再让模型按证据说话。  
   **复习标签：** #RAG #评测

2. **Q：** LoRA 的参数为什么少？  
   **A：** LoRA 冻结原始权重，只训练低秩增量矩阵。它把大矩阵更新拆成两个小矩阵，因此训练参数和显存开销都明显下降，适合资源有限的领域适配。  
   **一句话记忆法：** 不改整张地图，只学一条修正路线。  
   **复习标签：** #LoRA #微调

3. **Q：** Agent 和普通 LLM 应用有什么区别？  
   **A：** 普通 LLM 应用多是一次输入输出，Agent 会围绕目标进行多步决策，并调用工具观察外部环境。工程重点是工具边界、状态管理、失败恢复和评测。  
   **一句话记忆法：** LLM 回答，Agent 做事。  
   **复习标签：** #Agent #工具调用

4. **Q：** 模型评测为什么要分层？  
   **A：** 因为最终答案错误可能来自数据、检索、排序、上下文、生成或提示词。如果只看最终分数，很难知道该优化哪一层。  
   **一句话记忆法：** 先定位病灶，再开药。  
   **复习标签：** #模型评测 #RAG

5. **Q：** 部署大模型时最常见的瓶颈是什么？  
   **A：** 常见瓶颈是显存、吞吐、延迟和成本。面试时可以从 batch、KV cache、量化、并发控制和降级策略几个角度回答。  
   **一句话记忆法：** 能跑只是开始，跑得稳和便宜才是部署。  
   **复习标签：** #模型部署 #推理优化

## 4. 今日练习任务

### 4.1 算法题
- 题目：Top K 高频元素。
- 思路：用哈希表统计频率，再用大小为 k 的小根堆维护最高频元素。
- 复杂度：时间 O(n log k)，空间 O(n)。
- Python 参考代码：

```python
from collections import Counter
import heapq

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    heap = []
    for num, freq in Counter(nums).items():
        heapq.heappush(heap, (freq, num))
        if len(heap) > k:
            heapq.heappop(heap)
    return [num for _, num in heap]
```

### 4.2 大模型理论题
- 题目：为什么 decoder-only 模型适合生成任务？
- 参考答案：decoder-only 模型用因果注意力建模从左到右的 token 条件概率，训练目标和推理时逐 token 生成一致，因此适合对话、续写和代码生成。它结构统一，便于规模化训练和 KV cache 推理优化，但长上下文成本较高，理解类任务也需要通过 prompt 转换。
- 可能追问 1：为什么不能看未来 token？答：生成时未来 token 不存在，训练时用因果 mask 保持一致。
- 可能追问 2：KV cache 有什么作用？答：缓存历史 token 的 key/value，避免每步重复计算。

### 4.3 项目任务
给 RAG 项目加一个最小评测闭环：整理 20 条 query，每条包含标准答案和支持文档片段；跑当前 RAG，记录 top-5 是否命中证据、答案是否引用证据、是否幻觉。验收标准是能输出一张 bad case 表，并把失败原因分成召回失败、重排失败、生成失败三类。

## 5. 今日 60 秒背诵版

RAG 答不好时，我会先分层定位，而不是直接调 prompt。第一层看召回，确认 top-k 里有没有支持答案的证据；第二层看排序，判断关键证据是否被 rerank 放到前面；第三层看上下文组装，检查 chunk 是否过碎、过长或被截断；最后才看生成 prompt 是否要求引用证据和无证据拒答。在项目里，我会把 query、召回结果、rerank 分数、最终上下文和模型回答都记录下来，用 bad case 判断到底该优化 embedding、切分、rerank 还是提示词。
"""
