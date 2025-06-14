import numpy as np
import pandas as pd

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
    df["price_score"] = np.where((df[col_nb_bathroom] == -1) | (df[col_nb_bedroom] == -1), 
                                 np.nan,    
                                 np.where(df[col_nb_bathroom] == 1,
                                 (df[col_nb_bedroom] + df[col_nb_bathroom]/3)/df[col_price],
                                 # if there are more than 1 bathroom, we assume there's one ensuite room
                                 (df[col_nb_bedroom] + (df[col_nb_bathroom]-1)/3)/df[col_price]))
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
                                   (df[col_nb_bathroom] - 1)/df[col_nb_bedroom])
    # normalise score
    df["confort_score"] = np.minimum(df["confort_score"] * 10, 10)
    return df

def combined_score(df: pd.DataFrame,
                   col_price: str, 
                   col_nb_bedroom: str, 
                   col_nb_bathroom: str):
    df = price_score(df, col_price, col_nb_bedroom, col_nb_bathroom)
    df = confort_score(df, col_nb_bedroom, col_nb_bathroom)
    df["combined_score"] = df["price_score"] * df["confort_score"] / 10
    return df