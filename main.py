# main.py

import sys
from pathlib import Path

# 添加 src 到路径
SRC_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC_DIR))

from dotenv import load_dotenv
from finchatbi import FinChatBI

load_dotenv()

def main():
    print("🚀 FinChatBI 金融智能问答机器人已启动")
    print("💡 支持财报查询、股价查询等")
    print("📌 输入 'quit' 或 'exit' 退出\n")

    try:
        bot = FinChatBI(
            report_faiss_path="report_faiss_db",
            sqlite_db_path="databases/finance.db"
        )
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("\n请先构建所需数据：")
        print("  python build_db.py --report   # 构建财报向量库")
        print("  python build_db.py --stock    # 构建股价数据库")
        return

    while True:
        try:
            user_input = input("\n👤 请输入您的问题：").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 再见！")
                break
            if not user_input:
                continue

            response = bot.chat(user_input)
            print(f"\n🤖 {response}")

        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    main()