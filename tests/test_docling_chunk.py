from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker
import re
import json
import time


# ----------------------------
# 主题分类器
# ----------------------------

def classify_chunk(text: str, title_path: list):
    """根据标题路径和内容自动分类"""
    corpus = " ".join(title_path) + " " + text

    rules = {
        "management_discussion": ["管理层讨论", "经营情况", "分析", "讨论与分析"],
        "financial_analysis": ["财务状况", "利润", "成本", "费用", "毛利", "收入"],
        "cashflow": ["现金流", "经营活动产生", "投资活动", "筹资活动"],
        "risk": ["风险", "重大事项", "诉讼", "承诺", "不确定性"],
        "governance": ["治理", "董事会", "监事会", "内控", "审计"],
        "business_overview": ["主营业务", "行业情况", "产品", "市场", "区域"],
        "summary": ["重要提示", "摘要"],
        "notes": ["附注", "补充资料"]
    }
    for label, kws in rules.items():
        if any(kw in corpus for kw in kws):
            return label

    if "|" in text:  # Markdown 表格
        return "table"

    return "other"


# ----------------------------
# 处理超长段落（HierarchicalChunker 不会分割段落）
# ----------------------------

def split_long_text(text, max_len=600):
    if len(text) <= max_len:
        return [text]

    parts = re.split(r"\n\s*\n", text)
    new_chunks = []
    buf = ""

    for p in parts:
        if len(buf) + len(p) < max_len:
            buf += ("\n\n" + p) if buf else p
        else:
            if buf:
                new_chunks.append(buf)
            buf = p

    if buf:
        new_chunks.append(buf)

    return new_chunks


# ----------------------------
# 主函数：Markdown → 文档 → 层级 Chunk → 语义增强 → JSON
# ----------------------------

def chunk_markdown_with_docling(md_path: str):
    # Step1：文档解析
    converter = DocumentConverter()
    doc = converter.convert(md_path).document  # docling 结构化文档对象

    # Step2：层级 chunk
    chunker = HierarchicalChunker()
    raw_chunks = list(chunker.chunk(doc))

    final_chunks = []
    chunk_index = 0
    created_at = int(time.time())

    for c in raw_chunks:
        text = getattr(c, "text", "").strip()
        if not text:
            continue

        # 安全地获取 metadata，HierarchicalChunker 返回的 DocChunk 可能没有 metadata 属性
        meta = getattr(c, "metadata", {}) if hasattr(c, "metadata") else {}
        title_path = meta.get("title_path", []) if isinstance(meta, dict) else []
        
        # Step3：超长内容再次分块（HierarchicalChunker 不会分段）
        split_chunks = split_long_text(text)

        for part in split_chunks:
            chunk_type = classify_chunk(part, title_path)

            final_chunks.append({
                "chunk_id": f"ck_{chunk_index}",
                "chunk_index": chunk_index,
                "chunk_text": part,
                "title_path": title_path,
                "chunk_type": chunk_type,
                "created_at": created_at,
                "file_path": md_path
            })
            chunk_index += 1

    return final_chunks


# ----------------------------
# 执行 chunk（使用你的上传文件）
# ----------------------------

md_file = "E:/workspace/fin-report-reviewer/data/markdowns/MinerU_海康威视-2025半年报__20251115014014.md"

chunks = chunk_markdown_with_docling(md_file)

# 保存结果
output_path = "E:/workspace/fin-report-reviewer/data/chunks/海康威视-2025半年报_chunks.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"Chunk 完成，共 {len(chunks)} 个")
print("输出文件：", output_path)
