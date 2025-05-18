from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from src.database import db
# from ..src.database.db import SessionLocal, engine
# from .schema import TaskCreate, TaskResponse

rent_app = APIRouter()

def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()

@rent_app.get("/rent")
async def get_t(database: Session = Depends(get_db)):
    tasks = database.query(db.FlatsToRent).all()
    return tasks




# @tasks_app.get("/tasks")
# async def get_t(db: Session = Depends(get_db)):
#     tasks = db.query(db.FlatsToRent).all()
#     return tasks

# @tasks_app.post("/tasks/", response_model=TaskResponse)
# def create_task(task: TaskCreate, db: Session = Depends(get_db)):
#     db_task = tasks.Task(**task.dict())
#     db.add(db_task)
#     db.commit()
#     db.refresh(db_task)
#     return db_task

# @tasks_app.get("/tasks/{task_id}")
# async def get_one_task(task_id: int, db: Session = Depends(get_db)):
#     task = db.query(tasks.Task).filter_by(task_id = task_id).first()
#     return task

# @tasks_app.delete("/tasks/{task_id}")
# async def delete_task(task_id: int, db: Session = Depends(get_db)):
#     db.query(tasks.Task).filter_by(task_id = task_id).delete()
#     db.commit()
#     return f"deleted task:{task_id}"

# @tasks_app.delete("/tasks")
# async def delete_all(db: Session = Depends(get_db)):
#     db.query(tasks.Task).delete()
#     db.commit()
#     return "deleted all records"