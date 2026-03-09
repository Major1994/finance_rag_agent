# modules/ingest_reports.py

import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
import logging

logger = logging.getLogger(__name__)


def ingest_documents_to_vectorstore(
        documents: List[Document],
        vectorstore_path: str = "vectorstore",
        embedding_model_name: str = "BAAI/bge-fin-large-zh"
):
    """
    将文档列表向量化并保存到 FAISS 向量库（支持增量追加）。

    Args:
        documents: LangChain Document 列表
        vectorstore_path: 向量库存储路径
        embedding_model_name: Embedding 模型名称
    """
    if not documents:
        logger.warning("文档列表为空，跳过向量化。")
        return

    # 初始化 Embedding 模型
    model_kwargs = {"device": "cpu"}  # 可根据环境改为 "cuda"
    encode_kwargs = {"normalize_embeddings": True}
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=embedding_model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    vectorstore_path_obj = Path(vectorstore_path)

    if vectorstore_path_obj.exists():
        logger.info("加载现有向量库并追加新文档...")
        vectorstore = FAISS.load_local(
            vectorstore_path, embeddings, allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(documents)
    else:
        logger.info("创建新的向量库...")
        vectorstore = FAISS.from_documents(documents, embeddings)

    # 保存
    vectorstore.save_local(vectorstore_path)
    logger.info(f"✅ 向量库已保存至 {vectorstore_path}，共 {vectorstore.index.ntotal} 个向量")