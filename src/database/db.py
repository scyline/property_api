from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
# SQLite 连接（文件名为 tasks.db）
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FlatsToRent(Base):
    __tablename__ = "flats_to_rent"

    unique_id = Column(String(50), primary_key=True, index=True)
    location = Column(String(50), unique=False, nullable=False)
    property_type = Column(String(50))
    address = Column(String(100))
    rent = Column(String(50))
    price = Column(Integer)
    base = Column(String(50))
    number_of_bedroom = Column(Integer)
    number_of_bathroom = Column(Integer)
    description = Column(String(500))
    link = Column(String(100))
    run_time = Column(Date)


def init_db():
    # 删除旧数据库（仅测试时启用）
    # import os
    # if os.path.exists("./tasks.db"):
    #     os.remove("./tasks.db")

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 验证表和数据
    from sqlalchemy import inspect
    inspector = inspect(engine)
    print(f"已创建的表: {inspector.get_table_names()}")