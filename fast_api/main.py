from typing import Annotated
import uvicorn
from fastapi import Body, FastAPI
from pydantic import BaseModel
from fast_api.router import rent_app
from src.database.db import init_db

# 启动时创建表（确保只运行一次）
init_db()  # 👈 调用创建表的函数
app = FastAPI()

app.include_router(rent_app)

# 以下代码可以使用户直接利用uvicorn运行此web应用，只需python -m main
if __name__ == "__main__":
    uvicorn.run("fast_api.main:app")