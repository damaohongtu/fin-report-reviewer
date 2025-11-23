import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class HeadingInfo:
    level: int
    title: str
    line: str


@dataclass
class Block:
    type: str
    text: str
    level: Optional[int] = None
    heading_text: Optional[str] = None


class MarkdownChunker:
    """
    基于 Markdown 语法的财报分块器，具备以下特性：

    1. 识别 #/#-style 标题并维护 title_path，便于查询定位
    2. 段落/句子级别的安全切分，避免在句子中间截断
    3. 表格(<table>)整块保护，不拆分结构
    4. 对列表、引用、代码块等常见 Markdown 结构做保留
    """

    TABLE_PATTERN = re.compile(r"<table[\s\S]*?</table>", re.IGNORECASE)
    SENTENCE_PATTERN = re.compile(r".+?(?:[。！？!?；;．.](?!\d)|$)")

    def __init__(self, max_chunk_chars: int = 600, min_chunk_chars: int = 200):
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars

    def chunk_file(self, markdown_path: str) -> List[Dict]:
        text = Path(markdown_path).read_text(encoding="utf-8")
        return self.chunk_text(text, file_path=str(markdown_path))

    def chunk_text(self, markdown_text: str, file_path: str = "") -> List[Dict]:
        safe_text, table_map = self._extract_tables(markdown_text)
        blocks = self._split_into_blocks(safe_text)

        heading_stack: List[HeadingInfo] = []
        current_lines: List[str] = []
        current_length = 0
        chunks: List[Dict] = []
        chunk_index = 0
        created_at = int(time.time())

        def add_chunk(body: str):
            nonlocal chunk_index, current_lines, current_length
            body = body.strip()
            if not body:
                return
            title_path = [h.title for h in heading_stack]
            heading_lines = [h.line for h in heading_stack]
            chunk_text = self._compose_chunk_text(body, heading_lines)
            chunk_type = self._classify_chunk(chunk_text, title_path)

            chunks.append(
                {
                    "chunk_id": f"ck_{chunk_index}",
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "chunk_length": len(chunk_text),
                    "title_path": title_path,
                    "title": title_path[-1] if title_path else "",
                    "title_level": len(title_path),
                    "chunk_type": chunk_type,
                    "created_at": created_at,
                    "file_path": file_path,
                }
            )
            chunk_index += 1
            current_lines = []
            current_length = 0

        def flush_current_chunk():
            body = self._join_body(current_lines)
            if body:
                add_chunk(body)

        for block in blocks:
            if block.type == "heading":
                flush_current_chunk()
                self._update_heading_stack(heading_stack, block)
                continue

            if block.type == "table":
                flush_current_chunk()
                table_text = table_map.get(block.text.strip(), block.text)
                add_chunk(table_text)
                continue

            segments = self._block_to_segments(block)
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    continue

                if len(segment) > self.max_chunk_chars:
                    # 单段落/句子过长时，也保持完整（不截断句子），单独成块
                    flush_current_chunk()
                    add_chunk(segment)
                    continue

                if current_length and current_length + len(segment) + 2 > self.max_chunk_chars:
                    flush_current_chunk()

                current_lines.append(segment)
                current_length += len(segment) + 2

        flush_current_chunk()

        # 如果文档末尾只有标题没有内容，生成一个仅含标题的 chunk 以保留结构
        if not chunks and heading_stack:
            heading_only = "\n".join(h.line for h in heading_stack)
            chunks.append(
                {
                    "chunk_id": "ck_0",
                    "chunk_index": 0,
                    "chunk_text": heading_only,
                    "chunk_length": len(heading_only),
                    "title_path": [h.title for h in heading_stack],
                    "title": heading_stack[-1].title,
                    "title_level": len(heading_stack),
                    "chunk_type": "other",
                    "created_at": created_at,
                    "file_path": file_path,
                }
            )

        return chunks

    def _extract_tables(self, text: str) -> Tuple[str, Dict[str, str]]:
        tables: Dict[str, str] = {}

        def _replacer(match: re.Match) -> str:
            placeholder = f"[[TABLE_BLOCK_{len(tables)}]]"
            tables[placeholder] = match.group(0).strip()
            return f"\n{placeholder}\n"

        safe_text = self.TABLE_PATTERN.sub(_replacer, text)
        return safe_text, tables

    def _split_into_blocks(self, text: str) -> List[Block]:
        blocks: List[Block] = []
        buffer: List[str] = []
        buffer_type: Optional[str] = None
        in_code_block = False
        code_fence: Optional[str] = None

        lines = text.splitlines()
        for raw_line in lines:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if in_code_block:
                buffer.append(line)
                if stripped.startswith(code_fence or "```"):
                    in_code_block = False
                    blocks.append(Block("code", "\n".join(buffer)))
                    buffer, buffer_type = [], None
                continue

            if stripped.startswith("```") or stripped.startswith("~~~"):
                if buffer:
                    blocks.append(Block(buffer_type or "paragraph", "\n".join(buffer)))
                    buffer, buffer_type = [], None
                in_code_block = True
                code_fence = stripped[:3]
                buffer = [line]
                buffer_type = "code"
                continue

            if not stripped:
                if buffer:
                    blocks.append(Block(buffer_type or "paragraph", "\n".join(buffer)))
                    buffer, buffer_type = [], None
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                if buffer:
                    blocks.append(Block(buffer_type or "paragraph", "\n".join(buffer)))
                    buffer, buffer_type = [], None
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()
                blocks.append(Block("heading", stripped, level=level, heading_text=title_text))
                continue

            if stripped.startswith("[[TABLE_BLOCK_") and stripped.endswith("]]"):
                if buffer:
                    blocks.append(Block(buffer_type or "paragraph", "\n".join(buffer)))
                    buffer, buffer_type = [], None
                blocks.append(Block("table", stripped))
                continue

            if re.match(r"^(\*|-|\+)\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
                if buffer_type not in (None, "list"):
                    blocks.append(Block(buffer_type, "\n".join(buffer)))
                    buffer = []
                buffer_type = "list"
                buffer.append(line)
                continue

            # default paragraph accumulation
            if buffer_type not in (None, "paragraph"):
                blocks.append(Block(buffer_type, "\n".join(buffer)))
                buffer, buffer_type = [], None

            buffer_type = "paragraph"
            buffer.append(line)

        if buffer:
            blocks.append(Block(buffer_type or "paragraph", "\n".join(buffer)))

        return blocks

    def _block_to_segments(self, block: Block) -> List[str]:
        if block.type in {"paragraph", "list", "quote"}:
            text = block.text.strip()
            if not text:
                return []
            if len(text) <= self.max_chunk_chars:
                return [text]
            return self._split_by_sentence(text)

        if block.type == "code":
            return [block.text.strip("\n")]

        return [block.text]

    def _split_by_sentence(self, paragraph: str) -> List[str]:
        sentences = [s.strip() for s in self.SENTENCE_PATTERN.findall(paragraph) if s.strip()]
        if not sentences:
            return [paragraph]

        segments: List[str] = []
        buffer = ""
        for sent in sentences:
            if not buffer:
                buffer = sent
                continue

            candidate = f"{buffer} {sent}".strip()
            if len(candidate) <= self.max_chunk_chars:
                buffer = candidate
            else:
                segments.append(buffer)
                if len(sent) > self.max_chunk_chars:
                    # 句子本身超长，单独成段
                    segments.append(sent)
                    buffer = ""
                else:
                    buffer = sent

        if buffer:
            segments.append(buffer)

        return segments

    def _update_heading_stack(self, stack: List[HeadingInfo], block: Block):
        if block.level is None:
            return
        while stack and stack[-1].level >= block.level:
            stack.pop()
        stack.append(HeadingInfo(level=block.level, title=block.heading_text or "", line=block.text.strip()))

    def _compose_chunk_text(self, body: str, heading_lines: List[str]) -> str:
        body = body.strip()
        if not body:
            return "\n".join(heading_lines)
        if not heading_lines:
            return body
        header = "\n".join(heading_lines).strip()
        return f"{header}\n\n{body}"

    def _join_body(self, parts: List[str]) -> str:
        joined = "\n\n".join(part.strip("\n") for part in parts if part.strip())
        return joined.strip()

    def _classify_chunk(self, text: str, title_path: List[str]) -> str:
        lowered = text.lower()
        if "<table" in lowered and "</table>" in lowered:
            return "table"

        corpus = " ".join(title_path) + " " + text
        rules = {
            "management_discussion": ["管理层讨论", "经营情况", "分析", "讨论与分析"],
            "financial_analysis": ["财务状况", "利润", "成本", "费用", "毛利", "收入", "财务"],
            "cashflow": ["现金流", "经营活动产生", "投资活动", "筹资活动"],
            "risk": ["风险", "重大事项", "诉讼", "承诺", "不确定性"],
            "governance": ["治理", "董事会", "监事会", "内控", "审计"],
            "business_overview": ["主营业务", "行业情况", "产品", "市场", "区域"],
            "summary": ["重要提示", "摘要"],
            "notes": ["附注", "补充资料"],
        }

        for label, keywords in rules.items():
            if any(keyword in corpus for keyword in keywords):
                return label

        return "other"


def save_chunks_to_file(chunks: List[Dict], output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(chunks, fp, ensure_ascii=False, indent=2)


