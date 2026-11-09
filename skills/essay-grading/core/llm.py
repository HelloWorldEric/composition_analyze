"""DeepSeek 客户端封装：统一调用入口，带 JSON 模式与重试。"""
import json
import time

from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def chat(messages: list, json_mode: bool = False, max_retries: int = 2) -> str:
    """调用 DeepSeek，返回文本回复。json_mode=True 时强制 JSON 输出。"""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            kwargs = {
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 1.2,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = _client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()
        except Exception as e:  # 网络抖动 / 限流时重试
            last_err = e
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"DeepSeek 调用失败（已重试 {max_retries} 次）：{last_err}")


def chat_json(messages: list) -> dict:
    """调用 DeepSeek 并解析 JSON；解析失败自动补一次修复请求。"""
    text = chat(messages, json_mode=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = chat(
            [
                {"role": "system", "content": "将下面的内容修复为合法 JSON，只输出 JSON 本身。"},
                {"role": "user", "content": text},
            ],
            json_mode=True,
        )
        return json.loads(fixed)


def check_connection() -> tuple[bool, str]:
    """连通性测试：返回 (是否成功, 提示信息)。"""
    try:
        reply = chat(
            [{"role": "user", "content": "请回复：连接成功"}],
            max_retries=1,
        )
        return True, reply
    except Exception as e:
        return False, str(e)
