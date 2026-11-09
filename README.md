# 语文作文分析及修改智能体 📝

基于 DeepSeek 大模型的中学作文批改工具：模拟有 20 年教学经验的资深语文老师，对作文进行**结构化分析批改**与**升格修改**，支持文本、txt 文件、作文照片（OCR 识别）三种输入方式。

## 功能特性

- **三种输入方式**：上传 txt 文件、上传作文照片（多张，先 OCR 识别再人工校对）、直接粘贴文本
- **四维度评分（50 分制）**：立意与内容（20）、结构与思路（10）、语言表达（15）、书写与规范（5）
- **结构化批改报告**：总评、分维度评分、亮点（引用原文）、问题清单（病句/错别字/标点/用词不当等，定位到原句）、全文修改建议
- **升格修改**：基于分析结果改写作文，忠于原意、保留亮点、改动有据，逐条给出「原句 → 改为 → 理由」对照
- **报告导出**：一键生成 Markdown 格式的完整批改报告

## 项目结构

```
composition_analyze/
├── agent/                  # Streamlit Web 应用
│   ├── app.py              # Web 界面入口
│   ├── config.py           # 配置（.env 读取 API Key、模型参数）
│   ├── core/               # llm 客户端、analyzer 分析引擎、reviser 修改引擎、vision_ocr 图片识字
│   ├── prompts/            # 分析与修改提示词
│   └── samples/            # 示例作文
├── skills/essay-grading/   # 独立 CLI skill（不依赖 Streamlit，与 agent/ 并行独立）
│   ├── run.py              # CLI 入口
│   ├── core/               # 同 agent/core
│   └── prompts/            # 同 agent/prompts
└── 需求/                    # 需求文档
```

## 快速开始

### 1. 配置 API Key

在 `agent/` 或 `skills/essay-grading/` 目录下，复制 `.env.example` 为 `.env`，填入 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

> 照片识字需要账号下支持看图的视觉模型，默认 `deepseek-flash`，可通过 `DEEPSEEK_VISION_MODEL` 配置。

### 2a. Web 界面（agent/）

```bash
cd agent
pip install -r requirements.txt
streamlit run app.py
```

使用流程：上传/粘贴作文 → 「开始分析」→ 查看分析报告 → 「生成修改稿」→ 下载 Markdown 报告。

### 2b. 命令行（skills/essay-grading/）

```bash
cd skills/essay-grading
pip install -r requirements.txt

# 分析批改（输出 JSON）
python run.py analyze essay.txt

# 分析 + 升格修改（输出 JSON）
python run.py revise essay.txt

# 作文图片识字（支持多张，按页顺序）
python run.py ocr 页1.jpg 页2.jpg

# 一键生成完整 Markdown 批改报告
python run.py report essay.txt -o 报告.md
```

## 批改维度说明

| 维度 | 满分 | 评价要点 |
|---|---|---|
| 立意与内容 | 20 | 中心是否明确、选材是否恰当、内容是否充实 |
| 结构与思路 | 10 | 开头结尾、段落安排、过渡衔接、详略处理 |
| 语言表达 | 15 | 语句通顺度、词汇运用、修辞手法、是否有文采 |
| 书写与规范 | 5 | 错别字、标点使用、格式规范 |

## 注意事项

- 单篇作文建议不超过 3000 字（`MAX_ESSAY_CHARS` 可调），过长可能影响分析质量
- 图片识字结果请先人工校对再进入分析
- 升格修改必须以分析结果为依据，目标是提升一个档次的「学生水平好作文」，而非改写成满分范文腔

## 依赖

Python 3.10+，依赖见 [agent/requirements.txt](agent/requirements.txt)（openai、streamlit、python-dotenv）。
