from __future__ import annotations

import re


REQUIRED_SECTIONS = [
    "# 今日大模型实习面试日报",
    "## 1. 今日面试真题精讲",
    "## 2. 今日技术博客精读",
    "## 3. 今日必背问答卡片",
    "## 4. 今日练习任务",
    "## 5. 今日 60 秒背诵版",
    "## 6. 今日参考资料",
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

    errors.extend(_validate_reference_traceability(markdown))
    errors.extend(_validate_article_links(markdown))

    return errors


def _validate_reference_traceability(markdown: str) -> list[str]:
    errors: list[str] = []
    used_refs = set(re.findall(r"参考资料\s*\[(\d+)\]", markdown))
    listed_refs = set(re.findall(r"^-\s*\[(\d+)\]", markdown, flags=re.MULTILINE))
    missing_refs = sorted(used_refs - listed_refs, key=int)
    if missing_refs:
        errors.append(f"参考资料编号不可追溯：{', '.join(f'[{item}]' for item in missing_refs)}")
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
