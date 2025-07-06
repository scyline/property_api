from src.database.db import engine, insert_station_mapping_to_db, init_db
import pandas as pd
import logging
from sqlalchemy import text
from rapidfuzz import process, fuzz
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

def get_best_match(name, choices, scorer=fuzz.token_sort_ratio, threshold=70):
    match = process.extractOne(name, choices, scorer=scorer)
    if match and match[1] >= threshold:
        return match[0]
    return None

def map_naptan(df):
    # load mapping table
    df_naptan = pd.read_csv("./files/mapping/naptan.csv").drop(columns=["Unnamed: 0"], axis=1)
    df_naptan["commonName"] = df_naptan["commonName"].str.replace(" Underground Station","").str.replace(" Tram Stop","").str.replace(" DLR Station","")
    # create df of unique stations 
    l_stations = list(set(df["nearest_station"].unique()).union(set(df["second_nearest_station"].unique())))
    df_stations = pd.DataFrame(data=l_stations, columns=["station_name"])
    df_stations["station_name"] = df_stations["station_name"].str.replace(" Station","")
    # mapping & save df to local as csv file
    df_stations['matched_station'] = df_stations['station_name'].apply(lambda x: get_best_match(x, df_naptan['commonName']))
    df_final = df_stations.merge(df_naptan.drop_duplicates(subset=["commonName"]), left_on='matched_station', right_on='commonName', how='left')
    df_final = df_final.drop(columns=["commonName"], axis=1)
    df_final.to_csv("./files/mapping/stations_naptan.csv")
    return df_final

def prepare_stations_naptan_mapping():
    with engine.begin() as conn:
        try:
            result = conn.execute(text("SELECT nearest_station, second_nearest_station FROM flats_to_rent;"))
            df = pd.DataFrame(data=result, columns=["nearest_station","second_nearest_station"])
            result.close()
            df = map_naptan(df)
            return df
        except Exception:
            raise

def run_jobs(prepare_mapping_tb = True,
             save_mapping_to_db = False):
    
    if prepare_mapping_tb:
        # generate mapping table
        df = prepare_stations_naptan_mapping()
    
    if save_mapping_to_db:
        inspector = inspect(engine)
        if "station_code" not in inspector.get_table_names():
            init_db()
        # save mapping table to db
        df = pd.read_csv("./files/mapping/stations_naptan.csv")
        insert_station_mapping_to_db(df)


if __name__ == "__main__":

    # generate mapping table
    # run_jobs(True,False)

    # save mapping table to db
    run_jobs(False,True)