import uvicorn
from fastapi import Body, FastAPI
from app.router import rent_app
from src.database.db import init_db
from sqlalchemy import inspect
from src.database.db import engine

inspector = inspect(engine)
print(f"Tables in DB: {inspector.get_table_names()}")

# 启动时创建表（确保只运行一次）
if "flats_to_rent" not in inspector.get_table_names():
    init_db()

app = FastAPI()

app.include_router(rent_app)

# 以下代码可以使用户直接利用uvicorn运行此web应用，只需python -m main
if __name__ == "__main__":
    uvicorn.run("app.main:app")