from src.database.db import engine, insert_travel_time_to_db
import pandas as pd
import logging
from sqlalchemy import text
import requests

logger = logging.getLogger(__name__)

bank_station_code = "940GZZLUBNK"
aldgate_station_code = "940GZZLUALD"
liverpool_st_station_code = "940GZZLULVT"
tower_hill_station_code = "940GZZLUTWH"
tower_gateway_station_code = "9400ZZDLTWG"

dict_destination = {bank_station_code: 9,
             aldgate_station_code: 5,
             liverpool_st_station_code: 12,
             tower_hill_station_code: 10,
             tower_gateway_station_code: 10}

destination_name_mapping = {bank_station_code: "Bank",
             aldgate_station_code: "Aldgate",
             liverpool_st_station_code: "Liverpool Street",
             tower_hill_station_code: "Tower Hill",
             tower_gateway_station_code: "Tower Gateway"}

def get_journey_time(from_station, to_station="940GZZLUAGL"):
    url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{from_station}/to/{to_station}?date=20250710&time=0900&timeIs=Departing&journeyPreference=LeastTime&accessibilityPreference=NoRequirements&walkingSpeed=Average&cyclePreference=None"
    
    params = {}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        journey = data['journeys'][0]
        duration = journey['duration']
        return duration
    else:
        print(f"Error fetching journey from {from_station} to {to_station}")
        return None

def df_get_journey_time(df):
    dest_list = []
    dur_list = []
    walk_tome_list = []

    for _, row in df.iterrows():
        result_dict = {}
        for des, walk_time in dict_destination.items():
            try:
                dur = get_journey_time(row["station_code"], des)
                total_time = dur + walk_time
                result_dict[des] = total_time
            except Exception:
                result_dict[des] = float(60)  # In case of error, assign large number

        # Get the destination with minimum duration
        if result_dict:
            best_des = min(result_dict, key=result_dict.get)
            best_des_name = destination_name_mapping[best_des]
            best_dur = result_dict[best_des]
            best_wlk_tm = dict_destination[best_des]
        else:
            best_des_name = None
            best_dur = None
            best_wlk_tm = None

        dest_list.append(best_des_name)
        dur_list.append(best_dur - best_wlk_tm)
        walk_tome_list.append(best_wlk_tm)

        print(row["station_name"])
    
    df["best_destination"] = dest_list
    df["min_duration"] = dur_list
    df["walk_to_dest"] = walk_tome_list
    return df

def prepare_stations_naptan_mapping():
    with engine.begin() as conn:
        try:
            result = conn.execute(text("SELECT * FROM station_code WHERE station_code IS NOT NULL;"))
            df = pd.DataFrame(data=result, columns=["station_name","station_code"])
            result.close()
            df = df_get_journey_time(df)
            insert_travel_time_to_db(df)
            return df
        except Exception:
            raise

if __name__ == "__main__":
    df = prepare_stations_naptan_mapping()
    print(df)
    df.to_excel("/Users/sqwu/property_api/property_api/files/output/stations_travel_time.xlsx")
    # df = pd.read_excel("/Users/sqwu/property_api/property_api/files/output/stations_travel_time.xlsx")
    # try:
    #     insert_travel_time_to_db(df)
    # except Exception as e:
    #     raise e