import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import demo.dashboard_utils as util
warnings.filterwarnings('ignore') # To supress warnings
sns.set(style="darkgrid") # set the background for the graphs

df = util.load_data()

# Dashboard UI
st.title("🏠 Property Rental Dashboard")
st.sidebar.header("Filters")

# Filters
location_filter = st.sidebar.multiselect("Location", df['location'].unique())
price_range = st.sidebar.slider("Price Range (£)", float(df['price'].min()), float(df['price'].max()), (1000.0, 3000.0))

# Filter data
filtered_df = df[
    (df['location'].isin(location_filter) if location_filter else True) &
    (df['price'].between(price_range[0], price_range[1]))
]

# Key Metrics
st.header("Stats")
st.metric("Total Properties", len(filtered_df))
st.metric("Average Price (£)", f"{filtered_df['price'].mean():.2f}")

st.header("Price Heatmap (Bedrooms × Bathrooms)")

# Generate data
count_pivot, price_pivot = util.create_heatmap_data(df)

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
ax.set_title("Property Count (Text) vs Avg Price (Color)")
ax.set_xlabel("Bathrooms")
ax.set_ylabel("Bedrooms")

# Display in Streamlit
st.pyplot(plt.gcf())

# Price distribution by location
st.header("Price distribution by location")

location_list = df['location'].unique()
num_loc = len(location_list)
fig, ax_list = plt.subplots(num_loc, 1, figsize=(10, num_loc*3.4), dpi=100)

for i in range(num_loc):
    loc = location_list[i]
    ax = ax_list[i]
    util.price_dist(df, loc, fig, ax)
plt.tight_layout(pad=2.0)
st.pyplot(plt.gcf())

# Histogram of scores
st.header("Score distribution")
util.score_dist(df)
st.pyplot(plt.gcf())

# Data Table
st.header("Data")
st.dataframe(filtered_df.style.background_gradient(cmap='Blues'))