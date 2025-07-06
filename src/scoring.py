import numpy as np
import pandas as pd
from src.database.db import engine, insert_scores
from sqlalchemy import text
import src.const as const

def tanh_normalization(df: pd.DataFrame,
                       col_scores: str,
                       mean: float = 0.001):
    scores = df[col_scores].astype(float)
    
    # Center and scale
    centered = scores - scores.mean()
    scaled = centered / (scores.std() * 2) 
    #centered = scores - mean
    #scaled = centered / (0.00027 * 2)  # Adjust denominator to control spread
    
    print(f"mean: {scores.mean()}")
    print(f"std: {scores.std()}")
    # Apply tanh and rescale to [0,10]
    df[col_scores] = 5 * np.tanh(scaled) + 5
                          
    return df
                
def price_score(df: pd.DataFrame, 
                col_price: str, 
                col_nb_bedroom: str, 
                col_nb_bathroom: str):
    # when number of bedroom is missing, it is usually a studio flat
    df[col_nb_bedroom] = df[col_nb_bedroom].fillna('1').astype(int)
    # if no bathroom info available, fill with 1
    df[col_nb_bathroom] = df[col_nb_bathroom].fillna('1').astype(int)
    df[col_price] = df[col_price].astype(float)
    # calculate raw score
    df["price_score"] = np.where(df[col_nb_bathroom] == 1,
                                 (df[col_nb_bedroom] + df[col_nb_bathroom]/3)/df[col_price],
                                 # if there are more than 1 bathroom, we assume there's one ensuite room
                                 (df[col_nb_bedroom] + (df[col_nb_bathroom]-1)/3)/df[col_price])
    # normalise score
    df = tanh_normalization(df, "price_score", 1000)
    return df

def confort_score(df: pd.DataFrame, 
                col_nb_bedroom: str, 
                col_nb_bathroom: str):
    df[col_nb_bedroom] = df[col_nb_bedroom].astype(int)
    df[col_nb_bathroom] = df[col_nb_bathroom].astype(int)
    # calculate raw score
    df["confort_score"] = np.where(df[col_nb_bathroom] == 1,
                                   df[col_nb_bathroom]/df[col_nb_bedroom],
                                   # if there are more than 1 bathroom, we assume there's one ensuite room
                                   (df[col_nb_bathroom] - 1)/(df[col_nb_bedroom] - 1))
    # normalise score
    df["confort_score"] = np.minimum(df["confort_score"] * 10, 10)
    return df

def transport_score(df: pd.DataFrame):
    df["total_trans_tm"] = df["distance_to_station"] * 20 + df["travel_time"] + df["walk_time"]
    df["transport_score"] = np.where(df["total_trans_tm"].notna(),
                                     np.where(df["total_trans_tm"]<=20, 10,
                                              np.where(df["total_trans_tm"]<=30, 8,
                                                       np.where(df["total_trans_tm"]<=45, 6,
                                                                np.where(df["total_trans_tm"]<=60, 3.5, 1.5)))),
                                                                2)
    return df

def preprocess_df():
    with engine.begin() as conn:
        try:
            result_flats = conn.execute(text("SELECT * FROM flats_to_rent"))
            df_flats = pd.DataFrame(data=result_flats, columns=const.col_flat_to_rent)
            result_travel = conn.execute(text("SELECT * FROM stations_travel_time;"))
            df_travel = pd.DataFrame(data=result_travel, columns=const.col_travel)
            df_flats["nearest_station"] = df_flats["nearest_station"].str.replace(" Station","")
            # combine data
            df = pd.merge(df_flats,
                          df_travel,
                          left_on="nearest_station",
                          right_on="station_name",
                          how="left").drop(columns=["station_name"], axis=1)
            
            # format the distance values
            df["distance_to_station"] = df["distance_to_station"].str.replace(" miles", "", regex=False).astype(float)
            df["distance_to_second_station"] = df["distance_to_second_station"].str.replace(" miles", "", regex=False).astype(float)
            df["travel_time"] = df["travel_time"].astype(float)
            df["walk_time"] = df["walk_time"].astype(float)
            return df
        except Exception as e:
            raise e
        finally:
            conn.close()

def combined_score(df: pd.DataFrame,
                   col_price: str, 
                   col_nb_bedroom: str, 
                   col_nb_bathroom: str):
    df = price_score(df, col_price, col_nb_bedroom, col_nb_bathroom)
    df = confort_score(df, col_nb_bedroom, col_nb_bathroom)
    df = transport_score(df)
    df["combined_score"] = df["price_score"] * df["confort_score"] * df["transport_score"]/ 100
    return df

def score_flats_and_save_res():
    df = preprocess_df()
    df = combined_score(df, "price", "number_of_bedroom", "number_of_bathroom")
    insert_scores(df)
    return df

if __name__ == "__main__":
    df = score_flats_and_save_res()
    print(df.head(10))