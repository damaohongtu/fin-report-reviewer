"""
混合分块器 (HybridChunker)

结合多种分块策略：
1. 基于字符/Token的分块
2. 基于句子/段落的分块
3. 基于层次结构的分块（使用 HierarchicalChunker）
4. 支持重叠窗口

策略选择：
- 默认使用层次化分块（适用于结构化文档）
- 如果没有层次结构，回退到段落分块
- 对于超长段落，使用字符分块
"""

import re
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass
from pathlib import Path
from loguru import logger

try:
    from docling_core.transforms.chunker import HierarchicalChunker
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("docling 不可用，将使用基础分块策略")


@dataclass
class ChunkConfig:
    """分块配置"""
    chunk_size: int = 500  # 每块字符数
    overlap: int = 50  # 重叠字符数
    strategy: Literal["character", "sentence", "paragraph", "hierarchical", "hybrid"] = "hybrid"
    min_chunk_size: int = 50  # 最小块大小
    max_chunk_size: int = 2000  # 最大块大小
    preserve_boundaries: bool = True  # 是否保留边界（段落、句子）


class HybridChunker:
    """混合分块器
    
    支持多种分块策略的组合：
    - character: 固定字符数分块（带重叠）
    - sentence: 基于句子分块
    - paragraph: 基于段落分块
    - hierarchical: 使用 HierarchicalChunker（适用于结构化文档）
    - hybrid: 自动选择最佳策略
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """初始化分块器
        
        Args:
            config: 分块配置，如果为None则使用默认配置
        """
        self.config = config or ChunkConfig()
        self.hierarchical_chunker = None
        
        if DOCLING_AVAILABLE and self.config.strategy in ["hierarchical", "hybrid"]:
            try:
                self.hierarchical_chunker = HierarchicalChunker()
                logger.info("✅ 已初始化 HierarchicalChunker")
            except Exception as e:
                logger.warning(f"⚠️ HierarchicalChunker 初始化失败: {e}，将使用基础策略")
                self.hierarchical_chunker = None
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """分块文本
        
        Args:
            text: 输入文本
            metadata: 可选的元数据（如文档ID、标题等）
            
        Returns:
            chunks列表，每个chunk包含:
            - text: 文本内容
            - index: 索引
            - start_char: 起始字符位置
            - end_char: 结束字符位置
            - metadata: 元数据
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # 根据策略选择分块方法
        if self.config.strategy == "character":
            chunks = self._chunk_by_character(text)
        elif self.config.strategy == "sentence":
            chunks = self._chunk_by_sentence(text)
        elif self.config.strategy == "paragraph":
            chunks = self._chunk_by_paragraph(text)
        elif self.config.strategy == "hierarchical":
            chunks = self._chunk_hierarchical(text)
        elif self.config.strategy == "hybrid":
            chunks = self._chunk_hybrid(text)
        else:
            raise ValueError(f"未知的分块策略: {self.config.strategy}")
        
        # 添加元数据和索引
        result = []
        for idx, chunk_text in enumerate(chunks):
            # 计算字符位置
            start_char = text.find(chunk_text)
            end_char = start_char + len(chunk_text) if start_char >= 0 else len(chunk_text)
            
            result.append({
                "text": chunk_text.strip(),
                "index": idx,
                "start_char": start_char,
                "end_char": end_char,
                "metadata": {
                    **metadata,
                    "chunk_size": len(chunk_text),
                    "strategy": self.config.strategy
                }
            })
        
        logger.info(f"✅ 文本分块完成: {len(result)}个chunks (策略: {self.config.strategy})")
        return result
    
    def _chunk_by_character(self, text: str) -> List[str]:
        """基于字符数分块（带重叠）"""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.overlap
        step = chunk_size - overlap
        
        for i in range(0, len(text), step):
            chunk = text[i:i + chunk_size]
            if chunk.strip():  # 跳过空chunk
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """基于句子分块
        
        先按句子分割，然后合并到合适的chunk_size
        """
        # 中文句子分隔符
        sentence_pattern = r'[。！？；\n]+'
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果单个句子超过max_chunk_size，使用字符分块
            if len(sentence) > self.config.max_chunk_size:
                # 先保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk)
                # 对长句子进行字符分块
                char_chunks = self._chunk_by_character(sentence)
                chunks.extend(char_chunks)
                current_chunk = ""
                continue
            
            # 如果添加这个句子会超过chunk_size
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.config.chunk_size:
                chunks.append(current_chunk)
                # 保留重叠部分
                if self.config.overlap > 0 and len(current_chunk) > self.config.overlap:
                    current_chunk = current_chunk[-self.config.overlap:] + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """基于段落分块（类似 report_ingestion_service 中的实现）"""
        chunks = []
        
        # 按段落分割（中文段落通常用换行分隔）
        paragraphs = text.replace('\r\n', '\n').split('\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前段落加入后超过chunk_size
            if len(current_chunk) + len(paragraph) > self.config.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # 保留重叠部分
                    if self.config.overlap > 0 and len(current_chunk) > self.config.overlap:
                        current_chunk = current_chunk[-self.config.overlap:] + "\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 单个段落太长，使用字符分块
                    char_chunks = self._chunk_by_character(paragraph)
                    chunks.extend(char_chunks)
                    current_chunk = ""
            else:
                current_chunk += "\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_hierarchical(self, text: str) -> List[str]:
        """使用 HierarchicalChunker 进行层次化分块
        
        适用于包含标题、章节等结构的文档
        """
        if not self.hierarchical_chunker:
            logger.warning("HierarchicalChunker 不可用，回退到段落分块")
            return self._chunk_by_paragraph(text)
        
        try:
            # 将纯文本转换为 docling 的文档格式
            # 如果text是Markdown格式，可以直接使用
            # 否则尝试将其作为纯文本处理
            
            # 简单的Markdown检测
            is_markdown = bool(re.search(r'^#+\s|^\*\s|^-\s|```', text, re.MULTILINE))
            
            if is_markdown:
                # 尝试使用 HierarchicalChunker
                from docling.datamodel.document import Document
                from docling.document_converter import DocumentConverter
                
                # 创建临时Markdown文件
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                    f.write(text)
                    temp_path = f.name
                
                try:
                    converter = DocumentConverter()
                    doc = converter.convert(temp_path)
                    chunk_result = list(self.hierarchical_chunker.chunk(doc))
                    chunks = [chunk.text for chunk in chunk_result if chunk.text.strip()]
                    return chunks
                finally:
                    Path(temp_path).unlink(missing_ok=True)
            else:
                # 非Markdown文本，回退到段落分块
                logger.info("文本不是Markdown格式，使用段落分块")
                return self._chunk_by_paragraph(text)
                
        except Exception as e:
            logger.warning(f"HierarchicalChunker 处理失败: {e}，回退到段落分块")
            return self._chunk_by_paragraph(text)
    
    def _chunk_hybrid(self, text: str) -> List[str]:
        """混合策略：自动选择最佳分块方法
        
        1. 首先尝试层次化分块（如果文档有结构）
        2. 如果没有结构，使用段落分块
        3. 对于超长内容，使用字符分块
        """
        # 检测文档类型
        is_markdown = bool(re.search(r'^#+\s|^\*\s|^-\s|```', text, re.MULTILINE))
        
        if is_markdown and self.hierarchical_chunker:
            # 尝试层次化分块
            try:
                hierarchical_chunks = self._chunk_hierarchical(text)
                # 检查是否有合理的分块（至少2个chunk）
                if len(hierarchical_chunks) > 1:
                    return hierarchical_chunks
            except Exception as e:
                logger.debug(f"层次化分块失败: {e}，继续尝试其他策略")
        
        # 回退到段落分块
        return self._chunk_by_paragraph(text)
    
    def chunk_to_strings(self, text: str) -> List[str]:
        """分块并仅返回文本列表（简化接口）"""
        chunks = self.chunk(text)
        return [chunk["text"] for chunk in chunks]

