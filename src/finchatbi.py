# src/finchatbi.py

import os
import re
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.memory import ConversationBufferMemory
import logging

# 自定义 Embedding（调用 DashScope API）
from .embeddings import QwenEmbeddings

logger = logging.getLogger(__name__)

class FinChatBI:
    def __init__(
        self,
        report_faiss_path="report_faiss_db",
        sqlite_db_path="databases/finance.db"
    ):
        self.report_faiss_path = Path(report_faiss_path)
        self.sqlite_db_path = Path(sqlite_db_path)

        # 功能可用性标志
        self.rag_ready = False      # 财报 RAG 是否可用
        self.sql_ready = False      # 股价 NL2SQL 是否可用

        # 组件占位
        self.retriever = None
        self.rag_chain = None
        self.sql_agent = None

        # 初始化 Qwen LLM
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_key:
            raise ValueError("❌ 未设置 DASHSCOPE_API_KEY，请在 .env 中配置")
        self.llm = ChatTongyi(
            model="qwen-max",
            temperature=0.0,
            dashscope_api_key=dashscope_key
        )

        # === 尝试加载财报 RAG 向量库 ===
        if self.report_faiss_path.exists():
            try:
                self._load_rag()
                self.rag_ready = True
                logger.info("✅ 财报 RAG 向量库加载成功")
            except Exception as e:
                logger.error(f"❌ 财报向量库加载失败: {e}")
        else:
            logger.warning(f"⚠️ 财报向量库不存在: {self.report_faiss_path}")

        # === 尝试加载股价数据库 ===
        if self.sqlite_db_path.exists():
            try:
                self._load_sql_agent()
                self.sql_ready = True
                logger.info("✅ 股价数据库加载成功")
            except Exception as e:
                logger.error(f"❌ 股价数据库加载失败: {e}")
        else:
            logger.warning(f"⚠️ 股价数据库不存在: {self.sqlite_db_path}")

        # 对话记忆（可选）
        self.memory = ConversationBufferMemory(memory_key="chat_history", input_key="input")

    def _load_rag(self):
        """加载 FAISS 财报向量库（使用 DashScope Embedding）"""
        embeddings = QwenEmbeddings(model="text-embedding-v2")
        vectorstore = FAISS.load_local(
            str(self.report_faiss_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
        self.retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        self.rag_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": PromptTemplate.from_template("""
你是一个专业的金融分析师。请仅根据以下资料回答问题。
如果资料中没有相关信息，请回答：“根据现有资料无法确定。”
回答需简洁、准确，并注明来源（如文档名和页码）。

资料：
{context}

问题：{question}
回答：
""")
            }
        )

    def _load_sql_agent(self):
        """加载股价 NL2SQL Agent"""
        db_url = f"sqlite:///{self.sqlite_db_path.absolute()}"
        db = SQLDatabase.from_uri(db_url, sample_rows_in_table_info=1)
        self.sql_agent = create_sql_agent(
            llm=self.llm,
            db=db,
            agent_type="openai-tools",
            verbose=False,
            handle_parsing_errors=True,
            max_execution_time=10
        )

    def _route_query(self, query: str) -> str:
        """
        路由用户查询：
        - 'stock': 查询股价、成交量等 → NL2SQL
        - 'report': 查询财报、利润等 → RAG
        """
        q = query.lower()
        stock_words = ["股价", "价格", "收盘", "开盘", "最高", "最低", "成交量", "涨跌幅", "k线", "股票", "市值"]
        report_words = ["财报", "年报", "季报", "半年报", "净利润", "营收", "收入", "利润", "毛利率", "负债", "现金", "资产", "roe"]

        if any(w in q for w in stock_words):
            return "stock"
        elif any(w in q for w in report_words):
            return "report"
        else:
            return "report"  # 默认走 RAG（更安全）

    def chat(self, query: str) -> str:
        intent = self._route_query(query)
        logger.info(f"🔍 路由判断: '{query}' → {intent}")

        if intent == "stock":
            if not self.sql_ready:
                return "⚠️ 股价查询功能不可用。\n请先运行：\n  python build_db.py --stock"
            print("[执行] → NL2SQL（股价数据库）")
            try:
                res = self.sql_agent.invoke({"input": query})
                answer = res.get("output", "查询无结果").strip()
                source = "【数据来源】股价数据库"
            except Exception as e:
                answer = f"股价查询出错：{str(e)}"
                source = ""

        else:  # report
            if not self.rag_ready:
                return "⚠️ 财报查询功能不可用。\n请先运行：\n  python build_db.py --report"
            print("[执行] → RAG（财报向量库）")
            try:
                result = self.rag_chain({"query": query})
                answer = result["result"].strip()
                docs = result.get("source_documents", [])
                sources = list({
                    f"{d.metadata.get('source', '未知')} 第{d.metadata.get('page', '?')}页"
                    for d in docs
                })
                source = "；".join(sources) if sources else ""
                if source:
                    source = f"【数据来源】{source}"
            except Exception as e:
                answer = f"财报查询出错：{str(e)}"
                source = ""

        # 🔒 合规过滤：禁止投资建议
        if re.search(r"(买入|卖出|推荐|建议.*持有|加仓|减仓|看涨|看跌)", answer):
            answer = "根据合规要求，本系统不提供投资建议。"

        # 保存对话历史（可选）
        self.memory.save_context({"input": query}, {"output": answer})

        return f"{answer}\n\n{source}".strip()