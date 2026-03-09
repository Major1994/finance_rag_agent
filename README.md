# 📊 Finance RAG Agent — 金融智能问答系统

> 基于 **Qwen 大模型** 的本地化金融问答机器人  
> ✅ 财报 RAG（PDF 智能检索） + ✅ 股价 NL2SQL（自然语言查数据库）

---

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| **大语言模型 (LLM)** | `qwen-max`（阿里云 DashScope） |
| **文本嵌入 (Embedding)** | `text-embedding-v2`（阿里云 DashScope） |
| **向量检索** | FAISS（本地存储） |
| **结构化查询** | SQLite + LangChain SQL Agent |
| **PDF 解析** | `unstructured` + `pypdf` |
| **部署方式** | 单机 CLI（无需 Web 服务） |

## 📁 项目结构
├── build_db.py # 数据构建入口
├── main.py # 问答交互入口
├── report_faiss_db/ # 财报 FAISS 向量库
├── databases/finance.db # 股价 SQLite 数据库
├── data/
│ ├── financial_reports/ # 财报 PDF
│ └── stock_prices/ # 股价 CSV/Excel
└── src/ # 核心模块
    ├── finchatbi.py # 主问答 Agent
    ├── embeddings.py # Qwen Embedding 封装
    ├── build_report_rag.py # 构建财报向量库
    ├── load_stock_prices.py # 加载股价数据
    └── parse_reports.py # PDF 财报解析

## 🚀 快速开始

### 1. 克隆项目（如有）
```bash
git clone https://github.com/major1994/finance_rag_agent.git
cd finance_rag_agent
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 准备数据
将 财报 PDF 放入 data/financial_reports/
示例文件名：600519_2023年报.pdf
将 股价数据（CSV 或 Excel）放入 data/stock_prices/
必须包含列：symbol, date, open, high, low, close, volume

### 4. 构建数据资产
```
# 构建财报 RAG 向量库
python build_db.py --report

# 构建股价数据库
python build_db.py --stock
```

### 5. 启动问答
```commandline
python main.py
```

| 用户提问 | 系统响应 |
|--------|--------|
| 贵州茅台2023年净利润是多少？ | `619.54亿元`<br>【数据来源】600519_2023年报.pdf 第12页 |
| 宁德时代昨天收盘价多少？ | `185.30元`<br>【数据来源】股价数据库 |
| 比亚迪2023年营收同比增长多少？ | `34.2%`<br>【数据来源】002594_2023年报.pdf 第5页 |

