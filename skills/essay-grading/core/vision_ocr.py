"""图片识字模块：调用 deepseek 视觉模型识别作文图片中的文字。

支持多张图片按顺序识别后拼接，适合多页拍摄的作文。
"""
import base64

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_VISION_MODEL
from core.llm import _client

OCR_PROMPT = """请逐字识别这张作文图片中的文字，输出为纯文本，要求：
1. 按原文行列顺序完整转录，不要遗漏、不要改写、不要添加多余说明
2. 保留段落划分，每个段落之间空一行
3. 作文标题单独放第一行
4. 无法辨认的字用 ▢ 代替，不要猜测编造
5. 只输出识别出的文字内容"""


def recognize_text(image_bytes_list: list) -> str:
    """识别一或多张作文图片，返回拼接后的文本。

    Args:
        image_bytes_list: 图片二进制内容列表（png/jpg）
    """
    content = []
    for img in image_bytes_list:
        b64 = base64.b64encode(img).decode()
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        )
    content.append({"type": "text", "text": OCR_PROMPT})

    resp = _client.chat.completions.create(
        model=DEEPSEEK_VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        temperature=0.1,  # 识字需要稳定，不用 llm.chat 的 1.2
    )
    return resp.choices[0].message.content.strip()
