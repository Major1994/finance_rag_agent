# build_db.py

import sys
import argparse
from pathlib import Path

from src.build_report_rag import build_report_rag
from src.load_stock_prices import parse_and_load_stock_files

def main():
    parser = argparse.ArgumentParser(description="FinChatBI - 数据构建工具")
    parser.add_argument("--report", action="store_true", help="构建财报 RAG 向量库 (report_faiss_db/)")
    parser.add_argument("--stock", action="store_true", help="构建股价数据库 (databases/finance.db)")
    args = parser.parse_args()

    if not (args.report or args.stock):
        print("📌 请指定构建类型：")
        print("  --report   构建财报向量库")
        print("  --stock    构建股价数据库")
        return

    if args.report:
        print("📊 构建财报 RAG 向量库...")
        build_report_rag(report_faiss_path="report_faiss_db")
        print("✅ 财报向量库构建完成！")

    if args.stock:
        print("📈 构建股价数据库...")
        parse_and_load_stock_files(
            stock_dir="data/stock_prices",
            db_path="databases/finance.db"
        )
        print("✅ 股价数据库构建完成！")

if __name__ == "__main__":
    main()