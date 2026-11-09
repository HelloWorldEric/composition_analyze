"""分析引擎：调用 DeepSeek 对作文进行结构化批改。"""
from core.llm import chat_json
from prompts.analysis import ANALYSIS_SYSTEM, ANALYSIS_USER_TMPL


def analyze_essay(essay: str) -> dict:
    """分析作文，返回结构化报告 dict（结构见 prompts/analysis.py）。"""
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM},
        {"role": "user", "content": ANALYSIS_USER_TMPL.format(essay=essay)},
    ]
    return chat_json(messages)
