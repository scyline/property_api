# Property API & Dashboard 🏠

A Python-based project featuring:

1. **An interactive Streamlit dashboard** for exploring property listings in London — the main highlight.
2. **Custom scoring logic** to automatically recommend the best-fit properties, saving users time.
3. **A web scraper for Rightmove**, harvesting property data for further analysis.

---

## 📊 Streamlit Dashboard

Located in the `dashboard/` folder, this dashboard offers:

- **Best-fit property recommendation**, powered by a custom scoring algorithm that ranks listings based on user preferences and criteria.
- **Postcode heatmap** showing apartment counts per London postcode, with interactive tooltips.
- **Filters** for postcode, property type, nearest station, price, and number of images.
- **Tabular view** of filtered listings, displaying key metrics such as price, station distance, journey time, and overall score.
- **Interactive plots** (e.g., price distribution, image counts, score trends).
- **Folium map integration** for visualizing postcode zones and property locations.

**How it works**:  
1. Loads listing and station data from the database via SQLAlchemy (`src/database/db.py`).  
2. Uses your **scoring logic** to calculate a composite score for each listing (e.g., price per room, image availability, transit time, walkability).  
3. Users apply filters and sort by score to instantly view top recommendations.  
4. Results refresh dynamically — tables, visuals, and maps update in real time.

---

## 🤖 Scoring Logic (“Ideal Property”)

One of the core features of this project is the **property scoring engine**, which:

- Calculates a **composite score** based on multiple factors:
  - Journey time to city center
  - How many bathrooms compared to bedrooms in the property
  - Price relative to average postcode
  - Proximity to transport links
- Scores enable **instant identification of high-value properties** tailored to user needs.
- Reduces decision fatigue by surfacing top listings first, making property search efficient.

---

## 👀 Screenshots & Data
![alt text](<files/resource/Screenshot 2025-07-19 at 12.32.08-1.png>)

![alt text](<files/resource/Screenshot 2025-07-19 at 12.57.42.png>)

---

## 🧹 Web Scraping – `src/scrapping/`

A lightweight scraper targets Rightmove listing pages, collecting:

- **Basic info**: price, property type, postcode, description, bedroom/bathroom count, image count.
- **Station data**: nearest Tube/rail stations with distance.
- **Transit time**: relies on TfL API to compute journey duration to the nearest station.
- **Score-ready data**: scraped features feed directly into the scoring logic engine.

The dataset is cleaned, scored, and loaded into the backend database for visualization.

---

## ⚙️ Setup & Getting Started

```bash
git clone https://github.com/scyline/property_api.git
cd property_api

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/database/db.py

# Scrape Rightmove listings
python src/scrapping/scrape_rightmove.py

# Run the dashboard
streamlit run dashboard/app.py

```

---

## 🗄️ Data & Storage

- **SQLAlchemy** defines models in `src/database/models.py`, including tables such as `flats_to_rent` and optional lookup tables like `station_code`.
- **Engine config** handles database creation without overwriting existing data on reruns.

---

## ⚙️ Configuration

- `config.py`: Store API keys (e.g., TfL credentials), database URLs, scraping parameters, etc.
- `.env` file support recommended for keeping credentials secure.

---

## 🚀 Roadmap / Ideas

- ✏️ Add predicted rental price charts per postcode or station.
- 📷 Integrate more listing images as a gallery.
- 🌍 Support property search in other cities (e.g., Manchester, Birmingham).
- 📈 Add charts for price trends and supply statistics per zone.

---

## 💻 Tech Stack

- Python, Pandas, GeoPandas  
- SQLAlchemy (PostgreSQL/SQLite support)  
- Scrapy/Requests + BeautifulSoup for scraping  
- TfL Unified API for journey times  
- Streamlit + Folium for dashboard visualization  
- GeoJSON data for postcode boundary maps
