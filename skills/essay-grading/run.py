"""作文批改 skill 独立入口（不依赖 Streamlit）。

用法:
  python run.py analyze essay.txt                  # 分析批改，输出 JSON
  python run.py revise essay.txt                   # 分析 + 升格修改，输出 JSON
  python run.py ocr img1.jpg img2.jpg              # 图片识字
  python run.py report essay.txt -o 报告.md        # 分析+修改+汇总 Markdown 报告
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from config import MAX_ESSAY_CHARS, OUTPUT_DIR
from core.analyzer import analyze_essay
from core.reviser import revise_essay
from core.vision_ocr import recognize_text


def read_essay(path: str) -> str:
    raw = Path(path).read_bytes()
    for enc in ("utf-8", "gb18030", "big5"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def dump(obj, out: str | None):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
        print(f"已保存: {out}")
    else:
        print(text)


def build_report(essay: str, analysis: dict, revision: dict | None) -> str:
    lines = [
        "# 作文批改报告",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 一、作文原文",
        "",
        essay,
        "",
        "## 二、分析结果",
        "",
        f"- **标题**：{analysis.get('title', '-')}",
        f"- **体裁**：{analysis.get('genre', '-')}",
        f"- **主题**：{analysis.get('theme', '-')}",
        f"- **总分**：{analysis.get('total_score', '-')}/{analysis.get('full_score', 50)} 分",
        "",
        f"**总评**：{analysis.get('overall_comment', '')}",
        "",
        "### 分维度评分",
        "",
        "| 维度 | 得分 | 评价 |",
        "|---|---|---|",
    ]
    for d in analysis.get("dimensions", []):
        lines.append(f"| {d.get('name', '')} | {d.get('score', 0)}/{d.get('full', 0)} | {d.get('comment', '')} |")
    lines += ["", "### 亮点", ""]
    lines += [f"- {h}" for h in analysis.get("highlights", [])]
    lines += ["", "### 问题清单", ""]
    for i, issue in enumerate(analysis.get("issues", []), 1):
        lines += [
            f"{i}. **[{issue.get('type', '')}]** 「{issue.get('original', '')}」",
            f"   - 问题：{issue.get('problem', '')}",
            f"   - 建议：{issue.get('suggestion', '')}",
        ]
    lines += ["", "### 全文修改建议", ""]
    lines += [f"- {s}" for s in analysis.get("revision_suggestions", [])]
    if revision:
        lines += [
            "",
            "## 三、修改结果",
            "",
            f"**修改思路**：{revision.get('revision_summary', '')}",
            "",
            "### 修改后作文",
            "",
            revision.get("revised_essay", ""),
            "",
            "### 修改对照",
            "",
        ]
        for i, ch in enumerate(revision.get("changes", []), 1):
            lines += [
                f"{i}. 原句：{ch.get('original', '')}",
                f"   改为：{ch.get('revised', '')}",
                f"   理由：{ch.get('reason', '')}",
            ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="语文作文批改 skill")
    p.add_argument("command", choices=["analyze", "revise", "ocr", "report"])
    p.add_argument("inputs", nargs="+", help="txt/json 文件或图片（ocr 时可多张）")
    p.add_argument("-o", "--output", help="输出文件路径（默认打印到终端）")
    args = p.parse_args()

    if args.command == "ocr":
        images = [Path(f).read_bytes() for f in args.inputs]
        print(recognize_text(images))
        return

    essay = read_essay(args.inputs[0])
    if len(essay) > MAX_ESSAY_CHARS:
        print(f"警告：作文 {len(essay)} 字，超过建议上限 {MAX_ESSAY_CHARS} 字", file=sys.stderr)

    if args.command == "analyze":
        dump(analyze_essay(essay), args.output)
        return

    # revise / report：先分析再修改
    analysis = analyze_essay(essay)
    revision = revise_essay(essay, analysis)
    if args.command == "revise":
        dump(revision, args.output)
    else:
        md = build_report(essay, analysis, revision)
        out = args.output or str(OUTPUT_DIR / f"作文批改报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(md, encoding="utf-8")
        print(f"已保存: {out}")


if __name__ == "__main__":
    main()
