# scripts/build_vectorstore.py

import logging
from modules.parse_reports import parse_financial_reports
from modules.ingest_reports import ingest_documents_to_vectorstore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Step 1: 解析财报
    docs = parse_financial_reports(
        reports_dir="data/financial_reports",
        chunk_size=500,
        chunk_overlap=50
    )

    # Step 2: 向量化并入库
    if docs:
        ingest_documents_to_vectorstore(
            documents=docs,
            vectorstore_path="vectorstore",
            embedding_model_name="BAAI/bge-fin-large-zh"
        )
    else:
        print("⚠️ 无有效文档，未构建向量库。")