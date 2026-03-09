# modules/parse_reports.py

import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)


def parse_financial_reports(
        reports_dir: str = "data/financial_reports",
        chunk_size: int = 500,
        chunk_overlap: int = 50
) -> List[Document]:
    """
    批量解析指定目录下的所有 PDF 财报，返回分块后的 LangChain Document 列表。

    每个 Document 包含：
      - page_content: 文本内容
      - metadata: {"source": "filename.pdf", "page": 页码}

    Args:
        reports_dir: PDF 文件所在目录
        chunk_size: 分块大小
        chunk_overlap: 分块重叠长度

    Returns:
        List[Document]: 分块后的文档列表
    """
    pdf_files = glob.glob(os.path.join(reports_dir, "*.pdf"))
    if not pdf_files:
        logger.warning(f"在 {reports_dir} 中未找到任何 PDF 文件。")
        return []

    logger.info(f"发现 {len(pdf_files)} 份财报，开始解析...")

    all_docs = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    )

    for pdf_path in sorted(pdf_files):  # 确保顺序一致
        filename = os.path.basename(pdf_path)
        logger.info(f"正在解析: {filename}")
        try:
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()
            # 添加 source 元数据
            for doc in raw_docs:
                doc.metadata["source"] = filename
            chunks = text_splitter.split_documents(raw_docs)
            all_docs.extend(chunks)
        except Exception as e:
            logger.error(f"解析 {filename} 失败: {e}")

    logger.info(f"✅ 共解析出 {len(all_docs)} 个文本块。")
    return all_docs