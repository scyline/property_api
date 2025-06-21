import pandas as pd
import numpy as np
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import db
from src.scrapping import wrapper
import time 
import datetime

ts = time.time()

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
async def scrap_location(postcode: str,
                         loc_code: str,
                         database: Session = Depends(get_db),
                         pages: int = None):
    try:
        # Run the scraper
        logger.info(f"Starting scraping process for postcode: {postcode}, time: {datetime.datetime.now()}")
        if pages is not None:
            df_result = wrapper(postcode, loc_code, pages=pages)
        else:
            df_result = wrapper(postcode, loc_code)
        
        logger.info(f"Scraping process completed, time: {datetime.datetime.now()}")
        # Validate we got data
        if df_result.empty:
            logger.warning(f"No data found for postcode: {postcode}")
            return {"message": f"No properties found for {postcode}", "inserted_count": 0}
        
        inserted_count = len(df_result)
        
        return {
            "message": f"Successfully scraped and inserted {inserted_count} properties for {postcode}"
        }
    
    except Exception as e:
        logger.error(f"Error in scraping process for {postcode}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed for {postcode}: {str(e)}"
        )
    

@rent_app.get("/rent")
async def get_stats_basic(database: Session = Depends(get_db)):
    data = database.query(db.FlatsToRent).all()
    df = pd.DataFrame([r.__dict__ for r in data])
    if df.empty:
        logger.warning("No data found.")
        return {"message": "No properties found."}
    else:
        stats_global = df.groupby(["postcode"])["price"].agg(['count', 'min', 'max']).reset_index()
    
    # Convert to dictionary for JSON response
    stats_dict = stats_global.to_dict(orient='records')
    return {"statistics": stats_dict}


@rent_app.get("/rent/stats")
async def get_stat(database: Session = Depends(get_db),
                   postcode: str = None,
                   property_type: str = None,
                   number_of_bedroom: int = None,
                   number_of_bathroom: int = None):
    
    data = database.query(db.FlatsToRent).all()
    df = pd.DataFrame([r.__dict__ for r in data])
    if df.empty:
        logger.warning("No data found for the given condition(s)")
        return {"message": "No data found for the given condition(s)"}
    else:
        df["property_type"] = np.where(df["property_type"].isin(["Apartment", "Flat"]),
                                         "Apartment/Flat",
                                         df["property_type"])
    
    stats = df.groupby(["postcode",
                              "property_type",
                              "number_of_bedroom",
                              "number_of_bathroom"])["price"].agg(['mean', 'count', 'min', 'max']).reset_index()
    
    if postcode is not None:
        stats = stats[stats["postcode"] == postcode]

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
    postcode: str = None,
    property_type: str = None
):
    try:
        # Start with base query
        query = database.query(db.FlatsToRent)
        
        # Apply filters if provided
        if postcode:
            query = query.filter(db.FlatsToRent.postcode == postcode)
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
