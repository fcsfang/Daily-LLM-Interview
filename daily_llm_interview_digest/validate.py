from __future__ import annotations


REQUIRED_SECTIONS = [
    "# 今日大模型实习面试日报",
    "## 1. 今日面试真题精讲",
    "## 2. 今日技术博客精读",
    "## 3. 今日必背问答卡片",
    "## 4. 今日练习任务",
    "## 5. 今日 60 秒背诵版",
]

REQUIRED_QUESTION_FIELDS = [
    "**来源依据：**",
    "**可信度：**",
    "**考察点：**",
    "**面试口头版回答：**",
    "**深入理解版回答：**",
    "**常见追问与回答：**",
    "**项目联系：**",
    "**记忆关键词：**",
]


def validate_digest(markdown: str) -> list[str]:
    errors: list[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in markdown:
            errors.append(f"缺少必要结构：{section}")

    question_count = markdown.count("### 题目")
    if question_count < 3:
        errors.append("今日面试真题精讲少于 3 道题")
    if question_count > 5:
        errors.append("今日面试真题精讲超过 5 道题")

    for field in REQUIRED_QUESTION_FIELDS:
        if field not in markdown:
            errors.append(f"真题精讲缺少字段：{field}")

    card_count = markdown.count("一句话记忆法")
    if card_count < 5:
        errors.append("必背问答卡片少于 5 个")

    if "参考代码" not in markdown and "Python 参考代码" not in markdown:
        errors.append("今日练习任务缺少算法题参考代码")
    if "参考答案" not in markdown:
        errors.append("存在题目缺少参考答案")
    if "文章类型" not in markdown:
        errors.append("今日技术博客精读缺少文章类型")

    return errors
