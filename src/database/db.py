import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date
# SQLite 连接（文件名为 tasks.db）
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# Create a database connection using SQLAlchemy’s create_engine function.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
print(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FlatsToRent(Base):
    __tablename__ = "flats_to_rent"

    unique_id = Column(String(50), primary_key=True, index=True)
    postcode = Column(String(50), unique=False, nullable=False)
    property_type = Column(String(50))
    address = Column(String(100))
    rent = Column(String(50))
    price = Column(Integer)
    base = Column(String(50))
    number_of_bedroom = Column(Integer)
    number_of_bathroom = Column(Integer)
    description = Column(String(500))
    num_image = Column(Integer)
    link = Column(String(100))
    nearest_station = Column(String(200))
    distance_to_station = Column(String(50))
    second_nearest_station = Column(String(200))
    distance_to_second_station = Column(String(50))
    # price_score = Column(Float)
    # confort_score = Column(Float)
    # combined_score = Column(Float)
    run_time = Column(Date)

class Score(Base):
    __tablename__ = "scores"

    unique_id = Column(String(50), primary_key=True, index=True)
    price_score = Column(Float)
    confort_score = Column(Float)
    combined_score = Column(Float)


def init_db():
    # 删除旧数据库（仅测试时启用）
    # import os
    # if os.path.exists("./tasks.db"):
    #     os.remove("./tasks.db")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # 验证表和数据
    from sqlalchemy import inspect
    inspector = inspect(engine)
    print(f"Tables in DB: {inspector.get_table_names()}")



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_flats_table(session):
    try:
        session.query(FlatsToRent).delete()
        session.commit()
        print("✅ All records deleted from flats_to_rent.")
    except Exception as e:
        session.rollback()
        print("❌ Error deleting records:", e)
    finally:
        session.close()


def insert_dataframe_to_db(df):
    session = SessionLocal()

    try:
        flats = []
        for _, row in df.iterrows():
            flat = FlatsToRent(
                unique_id=row["unique_id"],
                postcode=row["postcode"],
                property_type=row["property_type"],
                address=row["address"],
                rent=row["rent"],
                price=row["price"],
                base=row["base"],
                number_of_bedroom=int(row["number_of_bedroom"]) if pd.notnull(row["number_of_bedroom"]) else None,
                number_of_bathroom=int(row["number_of_bathroom"]) if pd.notnull(row["number_of_bathroom"]) else None,
                description=row["description"],
                num_image=row["num_image"],
                link = row["link"],
                nearest_station=row["nearest_station"],
                distance_to_station=row["distance_to_station"],
                second_nearest_station=row["second_nearest_station"],
                distance_to_second_station=row["distance_to_second_station"],
                # price_score = row["price_score"],
                # confort_score = row["confort_score"],
                # combined_score = row["combined_score"],
                run_time=row["run_time"].date()
            )
            flats.append(flat)

        session.bulk_save_objects(flats)
        session.commit()
        print(f"✅ Inserted {len(flats)} records into the database.")
    except Exception as e:
        session.rollback()
        print("❌ Error inserting data:", e)
    finally:
        session.close()

def insert_scores(df):
    session = SessionLocal()

    try:
        scores = []
        for _, row in df.iterrows():
            score = Score(
                unique_id=row["unique_id"],
                price_score = row["price_score"],
                confort_score = row["confort_score"],
                combined_score = row["combined_score"]
            )
            scores.append(score)

        session.bulk_save_objects(scores)
        session.commit()
        print(f"✅ Inserted {len(scores)} records into the database.")
    except Exception as e:
        session.rollback()
        print("❌ Error inserting data:", e)
    finally:
        session.close()