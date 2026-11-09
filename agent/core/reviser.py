"""修改引擎：基于分析结果改写作文。"""
import json

from core.llm import chat_json
from prompts.revise import REVISE_SYSTEM, REVISE_USER_TMPL


def revise_essay(essay: str, analysis: dict) -> dict:
    """根据分析报告修改作文，返回 {revision_summary, revised_essay, changes}。"""
    messages = [
        {"role": "system", "content": REVISE_SYSTEM},
        {
            "role": "user",
            "content": REVISE_USER_TMPL.format(
                essay=essay, analysis=json.dumps(analysis, ensure_ascii=False, indent=2)
            ),
        },
    ]
    return chat_json(messages)
