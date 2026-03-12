import json
from langchain_community.embeddings import DashScopeEmbeddings
import numpy as np
import pickle
import tqdm
from langchain_community.vectorstores import FAISS
#初始化Dashscope Embeddings

from langchain_community.embeddings import DashScopeEmbeddings
embeddings =DashScopeEmbeddings(
    model="text-embedding-v1",
    dashscope_api_key="sk-cd5866becb3f4256856ddadbe549b5f9",
)
 
with open("../../company_list.txt", encoding="utf-8") as f:
    data=[line.strip() for line in f.readlines()]

db = FAISS.from_texts(data,embeddings)
with open("../../companyname_faiss_db", "wb") as f:
    pickle.dump(db,f)

with open("../../companyname_faiss_db", "rb") as f:
    db=pickle.load(f)
# 获取检索器，选择相关的检索结果 top-5
retriever = db.as_retriever(search_kwargs={"k": 5})
res=retriever.invoke("查询下广东广康的股价")
print (res)