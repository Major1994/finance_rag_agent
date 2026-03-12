import pandas as pd

csv_file = "../../data/stock_prices/上市公司基本信息.csv"
df = pd.read_csv(csv_file)

company = df["com_name"].to_list()

with open("../../company_list.txt","w",encoding="utf-8") as outf:
    for c in company:
        outf.write(c+"\n")