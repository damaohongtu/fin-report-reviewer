"""财报PDF文本解析器 - 专注于文本内容提取"""
import os
import re
from typing import Dict, Optional
from pathlib import Path

import pdfplumber
from loguru import logger


class FinancialPDFParser:
    """财报PDF文本解析器
    
    职责：
    - 提取PDF中的文本内容
    - 提取基本元数据（公司名称、报告期、报告类型）
    
    注意：不处理表格数据（表格由其他途径获取）
    """
    
    def __init__(self):
        """初始化解析器"""
        self.supported_formats = ['.pdf']
    
    def parse_financial_report(self, pdf_path: str) -> Dict:
        """解析财报PDF，提取文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            包含文本和元数据的字典:
            {
                "text": str,  # 全文文本
                "metadata": dict,  # 元数据（公司名称、报告期等）
                "page_count": int,  # 页数
                "file_size": int  # 文件大小（字节）
            }
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"开始解析财报PDF: {pdf_path}")
        
        # 提取文本内容
        text_content = self._extract_text(pdf_path)
        
        # 提取元数据
        metadata = self._extract_metadata(text_content)
        
        # 获取文件信息
        file_size = os.path.getsize(pdf_path)
        page_count = self._get_page_count(pdf_path)
        
        result = {
            "text": text_content,
            "metadata": metadata,
            "page_count": page_count,
            "file_size": file_size
        }
        
        logger.success(f"✅ PDF解析完成 - 共{page_count}页，提取{len(text_content)}字符")
        
        return result
    
    def _get_page_count(self, pdf_path: str) -> int:
        """获取PDF页数
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            页数
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.error(f"获取页数失败: {e}")
            return 0
    
    def _extract_text(self, pdf_path: str) -> str:
        """提取PDF文本内容
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        text_parts = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        # 清理文本：移除多余空白
                        text = self._clean_text(text)
                        if text:
                            text_parts.append(text)
                            logger.debug(f"提取第{page_num}页，{len(text)}字符")
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            raise
        
        full_text = '\n\n'.join(text_parts)
        logger.info(f"文本提取完成，共{len(full_text)}字符")
        
        return full_text
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白行
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # 保留非空行
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_metadata(self, text: str) -> Dict:
        """从文本中提取元数据（公司名称、报告期等）
        
        Args:
            text: PDF文本内容
            
        Returns:
            元数据字典
        """
        metadata = {
            "company_name": None,
            "report_period": None,
            "report_type": None
        }
        
        # 从文本前1000字符中提取关键信息
        header_text = text[:1000] if len(text) > 1000 else text
        
        # 提取公司名称（匹配中文公司名）
        company_pattern = r'([\u4e00-\u9fa5]+(?:股份)?(?:有限)?公司)'
        company_match = re.search(company_pattern, header_text)
        if company_match:
            metadata["company_name"] = company_match.group(1)
        
        # 提取报告期
        period_patterns = [
            (r'(\d{4})年度', 'year'),
            (r'(\d{4})年(\d{1,2})月', 'month'),
            (r'(\d{4})年[第一二三四]季度', 'quarter'),
            (r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})日?', 'date'),
        ]
        
        for pattern, period_type in period_patterns:
            match = re.search(pattern, header_text)
            if match:
                metadata["report_period"] = match.group(0)
                break
        
        # 提取报告类型
        if '年度报告' in header_text:
            metadata["report_type"] = "年报"
        elif '半年度报告' in header_text or '中期报告' in header_text:
            metadata["report_type"] = "半年报"
        elif '季度报告' in header_text:
            metadata["report_type"] = "季报"
        elif '招股说明书' in header_text:
            metadata["report_type"] = "招股书"
        
        logger.debug(f"提取元数据: {metadata}")
        
        return metadata

