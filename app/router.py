from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
from src.database import db
from src.scrapping import wrapper
# from ..src.database.db import SessionLocal, engine
# from .schema import TaskCreate, TaskResponse
import logging
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
rent_app = APIRouter()

def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()



@rent_app.post("/rent")
async def scrap_location(loc_name: str,
                         loc_code: str,
                         database: Session = Depends(get_db),
                         pages: int = None):
    try:
        # Run the scraper
        logger.info(f"Starting scraping process for location: {loc_name}")
        if pages is not None:
            df_result = wrapper(loc_name, loc_code, pages=pages)
        else:
            df_result = wrapper(loc_name, loc_code)
        
        # Validate we got data
        if df_result.empty:
            logger.warning(f"No data found for location: {loc_name}")
            return {"message": f"No properties found for {loc_name}", "inserted_count": 0}
        
        # Prepare data for insertion
        records = df_result.to_dict(orient='records')
        inserted_count = 0
        
        # Insert records in batches for better performance
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                database.bulk_insert_mappings(db.FlatsToRent, batch)
                database.commit()
                inserted_count += len(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
            except SQLAlchemyError as e:
                database.rollback()
                logger.error(f"Error inserting batch {i//batch_size + 1}: {str(e)}")
                # Try inserting records one by one to identify problematic records
                for record in batch:
                    try:
                        database.add(db.FlatsToRent(**record))
                        database.commit()
                        inserted_count += 1
                    except Exception as single_e:
                        database.rollback()
                        logger.error(f"Failed to insert record: {record}. Error: {str(single_e)}")
        
        logger.info(f"Scraping completed for {loc_name}. Inserted {inserted_count} new records")
        return {
            "message": f"Successfully scraped and inserted {inserted_count} properties for {loc_name}",
            "inserted_count": inserted_count,
            "total_found": len(df_result),
            "failed_inserts": len(df_result) - inserted_count
        }
    
    except Exception as e:
        logger.error(f"Error in scraping process for {loc_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed for {loc_name}: {str(e)}"
        )
    

@rent_app.get("/rent")
async def get_stats_basic(database: Session = Depends(get_db)):
    tasks = database.query(db.FlatsToRent).all()
    df_tasks = pd.DataFrame([task.__dict__ for task in tasks])
    stats_global = df_tasks.groupby(["location"])["price"].agg(['count', 'min', 'max']).reset_index()
    
    # Convert to dictionary for JSON response
    stats_dict = stats_global.to_dict(orient='records')
    return {"statistics": stats_dict}


@rent_app.get("/rent/stats")
async def get_stat(database: Session = Depends(get_db),
                   location: str = None,
                   property_type: str = None,
                   number_of_bedroom: int = None,
                   number_of_bathroom: int = None):
    
    tasks = database.query(db.FlatsToRent).all()
    df_tasks = pd.DataFrame([task.__dict__ for task in tasks])
    df_tasks["property_type"] = np.where(df_tasks["property_type"].isin(["Apartment", "Flat"]),
                                         "Apartment/Flat",
                                         df_tasks["property_type"])
    stats = df_tasks.groupby(["location",
                              "property_type",
                              "number_of_bedroom",
                              "number_of_bathroom"])["price"].agg(['mean', 'count', 'min', 'max']).reset_index()
    
    if location is not None:
        stats = stats[stats["location"] == location]

    if property_type is not None:
        stats = stats[stats["property_type"] == property_type]

    if number_of_bedroom is not None:
        stats = stats[stats["number_of_bedroom"] == number_of_bedroom]

    if number_of_bathroom is not None:
        stats = stats[stats["number_of_bathroom"] == number_of_bathroom]

    # Convert to dictionary for JSON response
    stats_dict = stats.to_dict(orient='records')
    return {"statistics": stats_dict}

        
@rent_app.delete("/rent")
async def delete_rentals(
    database: Session = Depends(get_db),
    location: str = None,
    property_type: str = None
):
    try:
        # Start with base query
        query = database.query(db.FlatsToRent)
        
        # Apply filters if provided
        if location:
            query = query.filter(db.FlatsToRent.location == location)
        if property_type:
            # Handle both "Apartment" and "Flat" if user searches for "Apartment/Flat"
            if property_type.lower() == "apartment/flat":
                query = query.filter(
                    db.FlatsToRent.property_type.in_(["Apartment", "Flat"])
                )
            else:
                query = query.filter(db.FlatsToRent.property_type == property_type)
        
        # Get count before deletion for reporting
        count = query.count()
        
        # Perform deletion
        query.delete(synchronize_session=False)
        database.commit()
        
        return {"message": f"Successfully deleted {count} records",
                "deleted_count": count}
    
    except Exception as e:
        database.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting records: {str(e)}"
        )


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