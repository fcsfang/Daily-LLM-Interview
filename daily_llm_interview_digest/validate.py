from __future__ import annotations

import re


REQUIRED_SECTIONS = [
    "# 今日大模型实习面试日报",
    "## 1. 今日面试真题精讲",
    "## 2. 今日技术博客精读",
    "## 3. 今日必背问答卡片",
    "## 4. 今日面试专项训练",
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

    if "参考答案" not in markdown:
        errors.append("存在题目缺少参考答案")
    if "文章类型" not in markdown:
        errors.append("今日技术博客精读缺少文章类型")
    if "### 4.1 大模型理论追问题" not in markdown:
        errors.append("今日面试专项训练缺少大模型理论追问题")
    if "### 4.2 项目表达任务" in markdown or "### 项目任务" in markdown:
        errors.append("今日面试专项训练不应包含项目任务")

    errors.extend(_validate_no_numbered_reference_only(markdown))
    errors.extend(_validate_article_links(markdown))

    return errors


def _validate_no_numbered_reference_only(markdown: str) -> list[str]:
    errors: list[str] = []
    if re.search(r"(参考资料|资料)\s*\[\d+\]", markdown):
        errors.append("参考资料应在使用处直接写标题和链接，不要只写编号引用")
    return errors


def _validate_article_links(markdown: str) -> list[str]:
    errors: list[str] = []
    in_blog_section = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line == "## 2. 今日技术博客精读":
            in_blog_section = True
            continue
        if in_blog_section and line.startswith("## "):
            in_blog_section = False
        if not in_blog_section or not line.startswith("**链接：**"):
            continue
        link_text = line.replace("**链接：**", "").strip()
        if link_text and not (
            link_text.startswith("http://")
            or link_text.startswith("https://")
            or link_text == "需进一步验证"
        ):
            errors.append(f"技术博客链接不可点击或未标注需验证：{link_text}")
    return errors
