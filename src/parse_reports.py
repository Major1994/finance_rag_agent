# src/parse_reports.py

"""
解析财务报告 PDF 文件，返回分块后的 LangChain Document 列表
支持中文财报，保留页码信息，过滤噪声
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title


def _is_noise_text(text: str) -> bool:
    """
    判断文本是否为噪声（页眉、页脚、页码、水印等）
    """
    text = text.strip()
    if not text:
        return True

    # 常见噪声模式
    noise_patterns = [
        r"^\d+$",  # 纯数字（页码）
        r"^[第]\s*\d+\s*[页张]$",  # "第123页"
        r"^\d+/\d+$",  # "1/10"
        r"公司名称|年度报告|半年度报告|季度报告",  # 重复标题
        r"©.*?保留所有权利",  # 版权声明
        r"confidential|机密",  # 敏感标记
        r"^\s*[\d\-\.\s]{5,}\s*$",  # 长串数字/符号（可能是页脚编号）
    ]

    for pattern in noise_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # 过短且无实质内容
    if len(text) < 5 and not any(c.isalpha() for c in text):
        return True

    return False


def parse_financial_reports(
        reports_dir: str = "data/financial_reports",
        chunk_size: int = 500,
        chunk_overlap: int = 50
) -> List[Document]:
    """
    解析指定目录下所有 PDF 财报，返回分块后的 Document 列表

    Args:
        reports_dir: PDF 文件所在目录
        chunk_size: 分块目标长度（字符数）
        chunk_overlap: 分块重叠长度

    Returns:
        List[Document]: 每个 Document 包含 page_content 和 metadata(source, page)
    """
    reports_path = Path(reports_dir)
    if not reports_path.exists():
        raise ValueError(f"财报目录不存在: {reports_path}")

    pdf_files = list(reports_path.rglob("*.pdf"))
    if not pdf_files:
        print(f"⚠️ 在 {reports_path} 中未找到 PDF 文件")
        return []

    all_documents = []

    for pdf_file in pdf_files:
        print(f"📄 正在解析: {pdf_file.name}")
        try:
            # 使用 unstructured 解析 PDF（自动选择策略）
            elements = partition_pdf(
                filename=str(pdf_file),
                strategy="auto",  # 自动选择 fast / hi_res
                infer_table_structure=False,
                languages=["chi_sim", "eng"]  # 支持中英文
            )

            # 过滤并收集有效文本
            clean_elements = []
            current_page = 1

            for el in elements:
                text = str(el).strip()
                if not text or _is_noise_text(text):
                    continue

                # 尝试从 element 获取页码（unstructured 可能提供）
                page_num = getattr(el.metadata, 'page_number', current_page)
                if page_num != current_page:
                    current_page = page_num

                clean_elements.append((text, current_page))

            if not clean_elements:
                print(f"⚠️ {pdf_file.name} 未提取到有效内容")
                continue

            # 合并相邻小段落（避免碎片化）
            merged = []
            buffer = ""
            last_page = 1
            for text, page in clean_elements:
                if len(buffer) + len(text) < 300:  # 小于阈值则合并
                    buffer += "\n" + text
                    last_page = page
                else:
                    if buffer:
                        merged.append((buffer.strip(), last_page))
                    buffer = text
                    last_page = page
            if buffer:
                merged.append((buffer.strip(), last_page))

            # 转为 Document 列表
            docs = [
                Document(
                    page_content=text,
                    metadata={
                        "source": pdf_file.name,
                        "page": page
                    }
                )
                for text, page in merged
            ]

            # 使用 LangChain 内置分块器进一步切分（按标题+长度）
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", "。", "；", " ", ""]
            )
            split_docs = text_splitter.split_documents(docs)

            all_documents.extend(split_docs)
            print(f"  → 提取 {len(split_docs)} 个文本块")

        except Exception as e:
            print(f"❌ 解析失败 {pdf_file.name}: {e}")
            continue

    print(f"✅ 总共解析 {len(all_documents)} 个文档块")
    return all_documents