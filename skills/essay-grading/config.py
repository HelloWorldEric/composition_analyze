"""全局配置：从 .env 读取 API Key 与模型参数。"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
# 视觉模型（用于作文图片识字），账号下支持看图的模型
DEEPSEEK_VISION_MODEL = os.getenv("DEEPSEEK_VISION_MODEL", "deepseek-flash")

# 单次请求作文最大字符数（超过则提示用户截断）
MAX_ESSAY_CHARS = 3000

OUTPUT_DIR = Path(__file__).parent / "outputs"
SAMPLES_DIR = Path(__file__).parent / "samples"
