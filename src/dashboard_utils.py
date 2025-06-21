import pandas as pd
from src.database import db
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings('ignore') # To supress warnings
sns.set(style="darkgrid") # set the background for the graphs

def load_data():
    # Example: Fetch from SQLite, CSV, or API
    database = db.SessionLocal()
    data = database.query(db.FlatsToRent).all()
    df = pd.DataFrame([task.__dict__ for task in data])
    df = df.drop(columns=["_sa_instance_state"], axis=1)
    return df

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
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 10), dpi=100)

    # Data to plot
    scores = {
        'Combined Score': df['combined_score'],
        'Price Score': df['price_score'],
        'Comfort Score': df['confort_score']
    }

    colors = {
        'Combined Score': '#FF4B4B',
        'Price Score': '#4BFF4B',
        'Comfort Score': '#4B4BFF'
    }

    # Plot each histogram in its own subplot
    for ax, (name, data) in zip([ax1, ax2, ax3], scores.items()):
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
