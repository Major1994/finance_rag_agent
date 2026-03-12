import sqlite3
import csv
import sys
from typing import Optional


def create_connection(db_file: str) -> Optional[sqlite3.Connection]:
    """ 创建 SQLite 数据库连接 """
    try:
        conn = sqlite3.connect(db_file)
        print("成功连接到数据库！")
        return conn
    except sqlite3.Error as e:
        print(f"连接数据库时出错：{e}")
        return None


def create_table(conn: sqlite3.Connection, table_name: str, headers: list):
    """ 根据 CSV 文件头创建表 """
    try:
        # 将字段名转换为 SQL 语句中的列定义 
        columns = ", ".join([f'"{header}" TEXT' for header in headers])
        sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns})'
        conn.execute(sql)
        print(f"成功创建表 {table_name}！")
    except sqlite3.Error as e:
        print(f"创建表时出错：{e}")


def insert_data(conn: sqlite3.Connection, table_name: str, rows: list, headers: list):
    """ 插入数据到表中 """
    try:
        # 准备占位符 
        placeholders = ", ".join(["?"] * len(headers))
        # 准备 SQL 插入语句 
        sql = f'INSERT INTO "{table_name}" VALUES ({placeholders})'

        # 执行批量插入 
        conn.executemany(sql, rows)
        conn.commit()
        print(f"成功插入 {len(rows)} 条记录！")
    except sqlite3.Error as e:
        print(f"插入数据时出错：{e}")


def csv_to_sqlite(csv_file: str, db_file: str, table_name: str):
    """ 主函数 """
    try:
        # 读取 CSV 文件 
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            headers = next(reader)  # 获取表头 
            rows = list(reader)  # 获取所有数据行

        # 创建数据库连接 
        conn = create_connection(db_file)
        if conn is None:
            return

            # 创建表
        create_table(conn, table_name, headers)

        # 插入数据 
        insert_data(conn, table_name, rows, headers)

        # 关闭连接 
        conn.close()
        print("数据库连接已关闭！")

    except FileNotFoundError as e:
        print(f"文件未找到：{e}")
    except Exception as e:
        print(f"程序运行时出错：{e}")


if __name__ == "__main__":
    # 解析命令行参数 
    # if len(sys.argv) != 4:
    #     print("使用方法：python csv_to_sqlite.py <CSV文件路径> <数据库文件路径> <表名>")
    #     sys.exit(1)

    csv_file = "../../data/stock_prices/股票日线.csv"
    db_file = "../../stock.db"
    table_name = "stock_price"

    csv_to_sqlite(csv_file, db_file, table_name)

    csv_file = "../../data/stock_prices/上市公司基本信息.csv"
    db_file = "../../stock.db"
    table_name = "company_info"

    csv_to_sqlite(csv_file, db_file, table_name)
