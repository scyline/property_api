import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import streamlit.components.v1 as components
from dashboard.utils import load_data, score_dist, price_dist, create_heatmap_data, london_heatmap
warnings.filterwarnings('ignore') # To supress warnings
sns.set(style="darkgrid") # set the background for the graphs

df = load_data()
df["price_per_room"] = np.where(df["number_of_bedroom"].isna(),
                                df["price"],
                                df["price"]/df["number_of_bedroom"])

# Dashboard UI
st.title("🏠 Property Rental Dashboard")
st.sidebar.header("Filters")

# Filters
location_filter = st.sidebar.multiselect("Postcode", df['postcode'].unique())
property_type_filter = st.sidebar.multiselect("Property type", df['property_type'].unique())
# num_img_filter = st.sidebar.multiselect("Number of images", df['num_image'].unique())
station_filter = st.sidebar.multiselect("Nearest station", df['nearest_station'].unique())
price_range = st.sidebar.slider("Price Range (£)", float(df['price'].min()), float(df['price'].max()), (650.0, 6000.0))
num_img_range = st.sidebar.slider("Number of images range", 0.0, float(df['num_image'].max()), (0.0, float(df['num_image'].max())))

# Filter data
filtered_df = df[
    (df['postcode'].isin(location_filter) if location_filter else True) &
    (df['property_type'].isin(property_type_filter) if property_type_filter else True) &
    # (df['num_image'].isin(num_img_filter) if num_img_filter else True) &
    (df['nearest_station'].isin(station_filter) if station_filter else True) &
    (df['price'].between(price_range[0], price_range[1])) &
    (df['num_image'].astype(float).between(num_img_range[0], num_img_range[1]))
]

#---------------------------------------------------------------------#
# Key Metrics
#---------------------------------------------------------------------#
st.header("Stats")
st.metric("Total Properties", len(filtered_df))
st.metric("Average Price (£) per room", f"{filtered_df['price_per_room'].mean():.2f}")

#---------------------------------------------------------------------#
# Create London appartment heatmap
#---------------------------------------------------------------------#
london_heatmap(filtered_df)
components.html(open("map.html", 'r').read(), height=600)

#---------------------------------------------------------------------#
# Price distribution by location
#---------------------------------------------------------------------#
st.header("Price (per room) distribution by location")

postcode_list = df['postcode'].unique()
num_loc = len(postcode_list)
fig, ax_list = plt.subplots(num_loc, 1, figsize=(10, num_loc*3.4), dpi=100)

for i in range(num_loc):
    pc = postcode_list[i]
    ax = ax_list[i]
    price_dist(df, pc, fig, ax)
plt.tight_layout(pad=2.0)
st.pyplot(plt.gcf())

#---------------------------------------------------------------------#
# Bedroom x bathroom heatmap
#---------------------------------------------------------------------#
st.header("Price Heatmap (Bedrooms × Bathrooms)")

# Generate data
count_pivot, price_pivot = create_heatmap_data(df)

# Create the heatmap
plt.figure(figsize=(10, 6))
ax = sns.heatmap(
    count_pivot,  # Color scale based on avg price
    annot=price_pivot,  # Cell text shows property count
    fmt=".1f",  # Display counts as integers
    cmap="YlOrRd",
    linewidths=.5,
    cbar_kws={'label': 'Count'},
    mask=(count_pivot == 0)  # Hide cells with zero properties
)

# Customize labels
ax.set_title("Property Count vs Avg Price (Per Room)")
ax.set_xlabel("Bathrooms")
ax.set_ylabel("Bedrooms")

# Display in Streamlit
st.pyplot(plt.gcf())

#---------------------------------------------------------------------#
# Histogram of scores
#---------------------------------------------------------------------#
st.header("Score distribution")
score_dist(filtered_df)
st.pyplot(plt.gcf())

#---------------------------------------------------------------------#
# Data Table
#---------------------------------------------------------------------#
st.header("Data")
st.dataframe(filtered_df.style.background_gradient(cmap='Blues'))