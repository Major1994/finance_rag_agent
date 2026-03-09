# src/build_report_rag.py

"""
构建财报 RAG 向量库：
1. 从 data/financial_reports/ 读取 PDF
2. 使用 parse_reports.py 分块
3. 调用 DashScope Embedding API (text-embedding-v2)
4. 存储为 FAISS 向量库 → report_faiss_db/
"""

import os
from pathlib import Path
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# 本地模块
from .parse_reports import parse_financial_reports
from .embeddings import QwenEmbeddings


def build_report_rag(
        reports_dir: str = "data/financial_reports",
        report_faiss_path: str = "report_faiss_db",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "text-embedding-v2"
) -> bool:
    """
    构建财报 RAG 向量库

    Args:
        reports_dir: 财报 PDF 所在目录
        report_faiss_path: FAISS 向量库存储路径
        chunk_size: 文本分块大小（字符数）
        chunk_overlap: 分块重叠长度
        embedding_model: Embedding 模型名（默认 text-embedding-v2）

    Returns:
        bool: 是否成功构建
    """
    reports_path = Path(reports_dir)
    output_path = Path(report_faiss_path)

    if not reports_path.exists():
        print(f"❌ 财报目录不存在: {reports_path}")
        return False

    pdf_files = list(reports_path.rglob("*.pdf"))
    if not pdf_files:
        print(f"⚠️ 未在 {reports_path} 中找到任何 PDF 文件")
        return False

    print(f"📄 发现 {len(pdf_files)} 份财报 PDF，开始解析...")
    try:
        documents: List[Document] = parse_financial_reports(
            reports_dir=reports_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    except Exception as e:
        print(f"❌ 财报解析失败: {e}")
        return False

    if not documents:
        print("⚠️ 未提取到有效文本内容")
        return False

    print(f"✅ 成功解析 {len(documents)} 个文本块")

    # 初始化 Embedding
    try:
        embeddings = QwenEmbeddings(model=embedding_model)
        print("☁️ 正在调用 DashScope Embedding API，请稍候...")
    except Exception as e:
        print(f"❌ Embedding 初始化失败: {e}")
        return False

    # 构建 FAISS 向量库
    try:
        vectorstore = FAISS.from_documents(documents, embeddings)
        print(f"🧠 向量库构建完成，正在保存至 {output_path}/")
        output_path.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(output_path))
        print("✅ 财报 RAG 向量库构建成功！")
        return True
    except Exception as e:
        print(f"❌ FAISS 保存失败: {e}")
        return False