import pandas as pd
from src.database import db
import folium
import geopandas as gpd
from folium.plugins import HeatMap
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import warnings
from sqlalchemy import text
from src.database.db import engine
import src.const as const
warnings.filterwarnings('ignore') # To supress warnings
sns.set(style="darkgrid") # set the background for the graphs

def load_data():
    # Example: Fetch from SQLite, CSV, or API
    # database = db.SessionLocal()
    # data = database.query(db.FlatsToRent).all()
    # df = pd.DataFrame([task.__dict__ for task in data])
    # df = df.drop(columns=["_sa_instance_state"], axis=1)

    with engine.begin() as conn:
        try:
            result_flats = conn.execute(text("SELECT * FROM flats_to_rent"))
            df_flats = pd.DataFrame(data=result_flats, columns=const.col_flat_to_rent)
            result_scores = conn.execute(text("SELECT * FROM scores;"))
            df_scores = pd.DataFrame(data=result_scores, columns=const.col_scores)
            # combine data
            df = pd.merge(df_flats,
                          df_scores,
                          on="unique_id",
                          how="left")
        except Exception as e:
            raise e
        finally:
            conn.close()
    return df


def london_heatmap(df):
    # Load your GeoJSON or shapefile
    geo_df = gpd.read_file("./files/london_postcodes.json")

    # Calculate apartments per postcode
    df_count_per_postcode = df.groupby(["postcode"])[["property_type"]].count().reset_index()
    df_count_per_postcode.columns = ["postcode", "count"]

    # Merge with apartment counts
    geo_df['postcode'] = geo_df['Name'].str.upper().str.strip()
    df_count_per_postcode['postcode'] = df_count_per_postcode['postcode'].str.upper().str.strip()
    merged = geo_df.merge(df_count_per_postcode, on='postcode', how='left')
    merged['count'] = merged['count'].fillna(0).astype(int)

    # Create base map
    m = folium.Map(location=[51.509865, -0.118092], zoom_start=12, tiles='cartodbpositron')

    # Add choropleth layer
    folium.Choropleth(
        geo_data=merged,
        data=merged,
        columns=['postcode', 'count'],
        key_on='feature.properties.postcode',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name='Number of Apartments',
    ).add_to(m)

    # Add postcode labels (postcode + count) at polygon centroid
    for _, row in merged.iterrows():
        if row['geometry'].is_empty or not row['geometry'].is_valid:
            continue
        centroid = row['geometry'].centroid
        if int(row['count']) > 0:
            popup_text = f"{row['postcode']}: {int(row['count'])}"
        else:
            popup_text = f"{row['postcode']}"
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f"""<div style="font-size:10px; color:#000000; text-align:center;">{popup_text}</div>"""
            )
        ).add_to(m)

    # Optional: Hover tooltip on each zone
    folium.GeoJson(
        merged,
        name="Postcodes",
        style_function=lambda x: {
            "fillOpacity": 0,
            "weight": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["postcode", "count"],
            aliases=["Postcode:", "Apartments:"],
            localize=True
        )
    ).add_to(m)

    # Save to HTML
    m.save("map.html")

    return m


# def london_heatmap(df):
#     # Load your GeoJSON or shapefile
#     geo_df = gpd.read_file("./files/london_postcodes.json")

#     # Calculate appartments per postcode
#     df_count_per_postcode = df.groupby(["postcode"])[["property_type"]].count().reset_index()
#     df_count_per_postcode.columns = ["postcode", "count"]

#     # Merge with apartment counts
#     geo_df['postcode'] = geo_df['Name'].str.upper()  # normalize case
#     merged = geo_df.merge(df_count_per_postcode, on='postcode', how='left')
#     merged['count'] = merged['count'].fillna(0)

#     # Create base map
#     m = folium.Map(location=[51.509865, -0.118092], zoom_start=10, tiles='cartodbpositron')

#     # Add choropleth
#     folium.Choropleth(
#         geo_data=merged,
#         data=merged,
#         columns=['postcode', 'count'],
#         key_on='feature.properties.postcode',
#         fill_color='YlOrRd',
#         fill_opacity=0.7,
#         line_opacity=0.2,
#         legend_name='Number of Apartments',
#     ).add_to(m)

#     # Add label tooltip
#     for _, row in merged.iterrows():
#         folium.GeoJsonTooltip(fields=['postcode', 'count']).add_to(folium.GeoJson(row['geometry']))

#     # Save map to HTML
#     m.save("map.html")

#     return

def create_heatmap_data(df):
    price = 'price_per_room'
    """Generate two pivot tables: counts and avg prices"""
    count_pivot = df.pivot_table(
        index='number_of_bedroom',
        columns='number_of_bathroom',
        values=price,
        aggfunc='count',
        fill_value=0
    ).sort_index(ascending=False)
    
    price_pivot = df.pivot_table(
        index='number_of_bedroom',
        columns='number_of_bathroom',
        values=price,
        aggfunc='mean',
        fill_value=0
    ).sort_index(ascending=False)
    
    return count_pivot, price_pivot

def price_dist(df, zone, fig, ax):
    price = 'price_per_room'
    df_plot = df[df['postcode'] == zone]
    mean = df_plot[price].mean()
    min = int(df[price].max())
    max = int(df[price].min())
    
    # Define your fixed range
    PRICE_RANGE = [max, min]
    N_BINS = 40  # Adjust bin count as needed
    
    # Create bins equally spaced across the fixed range
    bins = np.linspace(max, min, N_BINS+1)
    
    # Plot histogram with fixed bins
    ax.hist(df_plot[price], bins=bins, color='#FF4B4B', alpha=0.5)
    
    # Force x-axis limits
    ax.set_xlim(PRICE_RANGE)
    
    # Add mean line and label
    ax.axvline(mean, color='green', linestyle='--')
    ax.text(mean, ax.get_ylim()[1]*0.9, f'Mean: £{mean:.0f}',
            color='green', ha='center', fontsize=10)
    
    # Labels and title
    ax.set_xlabel('Monthly Rent (£)')
    ax.set_ylabel('Number of Properties')
    ax.set_title(f'Price distribution of {zone} (n={len(df_plot)})', fontsize=12, pad=10)
    
    # Add grid and clean up borders
    ax.grid(axis='y', alpha=0.3)


def score_dist(df):
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 10), dpi=100)

    # Data to plot
    scores = {
        'Combined Score': df['combined_score'],
        'Price Score': df['price_score'],
        'Comfort Score': df['confort_score'],
        'Transport Score': df['transport_score'],
    }

    colors = {
        'Combined Score': '#FF4B4B',
        'Price Score': '#4BFF4B',
        'Comfort Score': '#4B4BFF',
        'Transport Score': '#FF4BFF',
    }

    # Plot each histogram in its own subplot
    for ax, (name, data) in zip([ax1, ax2, ax3, ax4], scores.items()):
        # Plot histogram
        ax.hist(data, bins=20, color=colors[name], alpha=0.7, label=name)

        # Add mean line and text
        mean = data.mean()
        ax.axvline(mean, color=colors[name], linestyle='--', linewidth=1.5, alpha=0.8)
        ax.text(mean, ax.get_ylim()[1]*0.9, f'Mean: {mean:.2f}',
                color=colors[name], ha='center', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))

        # Customize each subplot
        ax.set_xlabel('Score Value', fontsize=10)
        ax.set_ylabel('Count', fontsize=10)
        ax.set_title(f'Distribution of {name}', fontsize=12, pad=10)
        ax.grid(True, linestyle='--', alpha=0.3)

        # Remove top/right spines
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)

        # Add legend
        ax.legend()

    # Adjust layout and spacing
    plt.tight_layout(pad=2.0)