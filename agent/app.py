"""语文作文分析及修改智能体 — Web 界面

运行: streamlit run app.py
"""
import json
from datetime import datetime

import streamlit as st

from config import DEEPSEEK_MODEL, MAX_ESSAY_CHARS, OUTPUT_DIR
from core.analyzer import analyze_essay
from core.llm import check_connection
from core.reviser import revise_essay
from core.vision_ocr import recognize_text

st.set_page_config(page_title="作文分析批改助手", page_icon="📝", layout="wide")

# ---------------- 会话状态 ----------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "revision" not in st.session_state:
    st.session_state.revision = None
if "essay" not in st.session_state:
    st.session_state.essay = ""
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

# ---------------- 侧边栏 ----------------
with st.sidebar:
    st.header("⚙️ 系统状态")
    if st.button("测试 DeepSeek 连接"):
        with st.spinner("连接中..."):
            ok, msg = check_connection()
        if ok:
            st.success(f"连接正常：{msg[:20]}")
        else:
            st.error(f"连接失败：{msg[:100]}")
    st.caption(f"模型：{DEEPSEEK_MODEL}")
    st.divider()
    st.markdown(
        "**使用流程**\n"
        "1. 上传 txt 或粘贴作文\n"
        "2. 点击「开始分析」\n"
        "3. 查看分析报告\n"
        "4. 点击「生成修改稿」\n"
        "5. 下载完整报告"
    )

# ---------------- 页头 ----------------
st.title("📝 语文作文分析及修改智能体")
st.caption("上传作文 → 智能批改分析 → 一键升格修改")

# ---------------- 输入区 ----------------
tab_upload, tab_image, tab_paste = st.tabs(["📄 上传 txt 文件", "📷 上传作文图片", "⌨️ 粘贴文本"])

uploaded = tab_upload.file_uploader("选择作文 txt 文件（UTF-8 编码）", type=["txt"])
if uploaded is not None:
    raw = uploaded.read()
    for enc in ("utf-8", "gb18030", "big5"):
        try:
            st.session_state.essay = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        st.session_state.essay = raw.decode("utf-8", errors="replace")

# ---- 图片输入：上传 → OCR 识别 → 人工校对 → 进入分析 ----
images = tab_image.file_uploader(
    "上传作文照片（支持多张，按页的顺序选择）",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)
if images:
    tabs_len = len(images)
    tab_image.caption(f"已选择 {tabs_len} 张图片")
    cols = tab_image.columns(min(tabs_len, 4))
    for i, img in enumerate(images):
        cols[i % 4].image(img, width="stretch")
    if tab_image.button("🔍 识别图片文字", type="primary", key="ocr_btn"):
        with st.spinner("正在识别图片中的文字..."):
            try:
                st.session_state.ocr_text = recognize_text([img.getvalue() for img in images])
            except Exception as e:
                st.session_state.ocr_text = ""
                tab_image.error(f"识别失败：{e}")
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""
if st.session_state.ocr_text:
    tab_image.markdown("**✅ 识别结果（请校对，识别不准的字可直接修改）**")
    ocr_edited = tab_image.text_area(
        "校对识别结果",
        value=st.session_state.ocr_text,
        height=260,
        key="ocr_edit",
        label_visibility="collapsed",
    )
    st.session_state.ocr_text = ocr_edited
    if tab_image.button("确认使用此文本", key="ocr_confirm"):
        st.session_state.essay = ocr_edited
        st.session_state.analysis = None
        st.session_state.revision = None
        tab_image.success("已确认识别文本，可点击「开始分析」")

paste = tab_paste.text_area(
    "在此粘贴作文内容",
    value=st.session_state.essay,
    height=240,
    key="paste_area",
)
if paste:
    st.session_state.essay = paste

essay = st.session_state.essay.strip()
if essay:
    n = len(essay)
    st.caption(f"当前字数：{n} 字" + ("" if n <= MAX_ESSAY_CHARS else f"（建议不超过 {MAX_ESSAY_CHARS} 字，过长可能影响分析质量）"))

col1, col2 = st.columns(2)
with col1:
    run_analysis = st.button("🔍 开始分析", type="primary", use_container_width=True, disabled=not essay)
with col2:
    run_revise = st.button(
        "✍️ 生成修改稿",
        type="primary",
        use_container_width=True,
        disabled=not (essay and st.session_state.analysis),
    )
if st.session_state.analysis is None:
    st.caption("提示：需先完成分析，才能生成修改稿")

# ---------------- 分析执行 ----------------
if run_analysis:
    st.session_state.revision = None
    with st.spinner("AI 老师正在批改作文，请稍候（约 30-60 秒）..."):
        try:
            st.session_state.analysis = analyze_essay(essay)
        except Exception as e:
            st.session_state.analysis = None
            st.error(f"分析失败：{e}")

# ---------------- 修改执行 ----------------
if run_revise:
    with st.spinner("AI 老师正在根据分析结果修改作文..."):
        try:
            st.session_state.revision = revise_essay(essay, st.session_state.analysis)
        except Exception as e:
            st.session_state.revision = None
            st.error(f"修改失败：{e}")

# ---------------- 分析报告渲染 ----------------
analysis = st.session_state.analysis
if analysis:
    st.divider()
    st.subheader("📋 分析报告")

    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric("总评分", f"{analysis.get('total_score', '-')} / {analysis.get('full_score', 50)}")
    c2.metric("体裁", analysis.get("genre", "-"))
    c3.metric("主题", analysis.get("theme", "-"))

    with st.expander("📖 原文", expanded=False):
        st.write(essay)

    st.markdown("**总评**")
    st.info(analysis.get("overall_comment", ""))

    st.markdown("**分维度评分**")
    for dim in analysis.get("dimensions", []):
        full = dim.get("full", 1) or 1
        score = dim.get("score", 0)
        with st.container(border=True):
            c_a, c_b = st.columns([1, 3])
            c_a.markdown(f"**{dim.get('name', '')}**  \n`{score}/{full}`")
            c_b.progress(min(score / full, 1.0), text=dim.get("comment", ""))

    colL, colR = st.columns(2)
    with colL:
        st.markdown("✅ **亮点**")
        for h in analysis.get("highlights", []):
            st.markdown(f"- {h}")
    with colR:
        st.markdown("💡 **全文修改建议**")
        for s in analysis.get("revision_suggestions", []):
            st.markdown(f"- {s}")

    st.markdown("⚠️ **问题清单**")
    for i, issue in enumerate(analysis.get("issues", []), 1):
        with st.container(border=True):
            st.markdown(
                f"**{i}. [{issue.get('type', '其他')}]** `{issue.get('original', '')}`"
            )
            st.markdown(f"- 问题：{issue.get('problem', '')}")
            st.markdown(f"- 建议：{issue.get('suggestion', '')}")

# ---------------- 修改结果渲染 ----------------
revision = st.session_state.revision
if revision:
    st.divider()
    st.subheader("✍️ 修改结果")
    st.markdown(f"**修改思路**：{revision.get('revision_summary', '')}")

    tab_rev, tab_chg = st.tabs(["📄 修改后作文", "🔍 修改对照"])
    with tab_rev:
        st.markdown(revision.get("revised_essay", ""))
    with tab_chg:
        for i, ch in enumerate(revision.get("changes", []), 1):
            with st.container(border=True):
                st.markdown(f"**{i}. 原句**：{ch.get('original', '')}")
                st.markdown(f"**改为**：{ch.get('revised', '')}")
                st.caption(f"理由：{ch.get('reason', '')}")

# ---------------- 报告导出内容 ----------------
def build_report(essay: str, analysis: dict, revision: dict | None) -> str:
    """将分析结果与修改结果汇总为 Markdown 报告。"""
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


# ---------------- 导出 ----------------
if analysis:
    st.divider()
    md = build_report(essay, analysis, revision)
    st.download_button(
        "⬇️ 下载完整报告 (Markdown)",
        data=md,
        file_name=f"作文批改报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
    )
