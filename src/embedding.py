# src/embeddings.py

"""
Qwen Embedding 封装（基于 DashScope API）
模型：text-embedding-v2
维度：1024
上下文：最大 6144 tokens
"""

import os
import time
from typing import List, Any
from langchain_core.embeddings import Embeddings
import dashscope
from dashscope import TextEmbedding

class QwenEmbeddings(Embeddings):
    """
    调用 DashScope 的 text-embedding-v2 模型生成向量
    兼容 LangChain 的 Embeddings 接口
    """

    def __init__(
        self,
        model: str = "text-embedding-v2",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 从环境变量加载 API Key
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "❌ DASHSCOPE_API_KEY 未设置。\n"
                "请在 .env 文件中添加：\n"
                "DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx"
            )
        dashscope.api_key = self.api_key

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成 embedding（支持最多 25 条文本/次）
        """
        if not texts:
            return []

        embeddings = []
        batch_size = 25  # DashScope 单次最大输入数

        for i in range(0, len(texts), batch_size):
            batch = [str(t).strip() for t in texts[i:i + batch_size] if t]
            if not batch:
                continue

            for attempt in range(self.max_retries):
                try:
                    resp = TextEmbedding.call(
                        model=self.model,
                        input=batch
                    )
                    if resp.status_code == 200:
                        batch_embeddings = [
                            item["embedding"] for item in resp.output["embeddings"]
                        ]
                        embeddings.extend(batch_embeddings)
                        break  # 成功则跳出重试
                    else:
                        error_msg = f"API 返回错误: {resp.code} - {resp.message}"
                        if attempt < self.max_retries - 1:
                            print(f"⚠️ {error_msg}，{self.retry_delay}秒后重试 ({attempt + 1}/{self.max_retries})")
                            time.sleep(self.retry_delay)
                        else:
                            raise RuntimeError(error_msg)
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        print(f"⚠️ 网络异常: {e}，{self.retry_delay}秒后重试 ({attempt + 1}/{self.max_retries})")
                        time.sleep(self.retry_delay)
                    else:
                        raise RuntimeError(f"Embedding 调用失败（已重试 {self.max_retries} 次）: {e}")

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        生成单条 query 的 embedding
        """
        return self.embed_documents([text])[0]

