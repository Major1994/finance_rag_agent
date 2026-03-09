# src/load_stock_prices.py

"""
加载并清洗股价数据，写入 SQLite 数据库
支持 CSV / Excel 文件，自动映射常见列名
输出表: stock_prices (symbol, date, open, high, low, close, volume)
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Union


def parse_and_load_stock_files(
        stock_dir: Union[str, Path],
        db_path: Union[str, Path]
) -> bool:
    """
    读取 stock_dir 下所有 CSV/Excel 文件，合并后写入 SQLite

    预期列（不区分大小写，支持常见别名）：
      - 股票代码: symbol, ticker, code, 股票代码
      - 日期: date, 日期, 交易日期
      - 开盘价: open, 开盘, 开盘价
      - 收盘价: close, 收盘, 收盘价
      - 最高价: high, 最高, 最高价
      - 最低价: low, 最低, 最低价
      - 成交量: volume, 成交量

    Args:
        stock_dir: 股价原始数据目录
        db_path: SQLite 数据库路径（如 databases/finance.db）

    Returns:
        bool: 是否成功加载并保存
    """
    stock_dir = Path(stock_dir)
    db_path = Path(db_path)

    if not stock_dir.exists():
        print(f"❌ 股价数据目录不存在: {stock_dir}")
        return False

    # 确保数据库父目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    all_dfs = []
    valid_files = 0

    for file_path in stock_dir.rglob("*"):
        if file_path.suffix.lower() not in [".csv", ".xlsx", ".xls"]:
            continue

        print(f"📄 读取: {file_path.name}")
        try:
            # 读取文件
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8-sig")  # 支持带 BOM 的 UTF-8
            else:
                df = pd.read_excel(file_path)

            if df.empty:
                print(f"⚠️ 跳过 {file_path.name}：文件为空")
                continue

            # 标准化列名：去空格 + 转小写
            df.columns = df.columns.astype(str).str.strip().str.lower()

            # 列名映射字典（支持中英文）
            col_mapping = {
                # 股票代码
                "股票代码": "symbol", "ticker": "symbol", "code": "symbol",
                # 日期
                "日期": "date", "交易日期": "date",
                # 价格
                "开盘价": "open", "开盘": "open",
                "收盘价": "close", "收盘": "close",
                "最高价": "high", "最高": "high",
                "最低价": "low", "最低": "low",
                # 成交量
                "成交量": "volume"
            }

            # 应用映射
            df = df.rename(columns=col_mapping)

            # 必需字段
            required_cols = ["symbol", "date", "open", "high", "low", "close", "volume"]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print(f"⚠️ 跳过 {file_path.name}：缺少列 {missing_cols}")
                continue

            # 数据清洗
            # 1. 日期标准化
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
            # 2. 数值列转为数字
            numeric_cols = ["open", "high", "low", "close", "volume"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            # 3. 去除含缺失值的行
            df = df.dropna(subset=required_cols)

            if df.empty:
                print(f"⚠️ 跳过 {file_path.name}：无有效数据行")
                continue

            # 仅保留所需列并追加
            all_dfs.append(df[required_cols].copy())
            valid_files += 1

        except Exception as e:
            print(f"❌ 解析失败 {file_path.name}: {e}")
            continue

    if not all_dfs:
        print("⚠️ 未找到任何有效的股价数据")
        return False

    # 合并所有数据
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"✅ 共加载 {len(combined_df)} 条记录（来自 {valid_files} 个文件）")

    # 写入 SQLite
    try:
        conn = sqlite3.connect(db_path)
        combined_df.to_sql("stock_prices", conn, if_exists="replace", index=False)
        conn.close()
        print(f"💾 已保存至 {db_path}")
        return True
    except Exception as e:
        print(f"❌ 数据库写入失败: {e}")
        return False