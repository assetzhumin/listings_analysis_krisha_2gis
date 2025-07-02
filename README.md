# LISTINGS\_ANALYSIS\_KRISHA\_2GIS

Real estate listings analytics from Krisha.kz and 2GIS: data collection, merging, analysis, and a Streamlit web app with a price estimation model.

## Features

- **Data Collection**: scrape Krisha.kz and 2GIS using Selenium, BeautifulSoup, and REST APIs
- **Cleaning & Merging**: build `filtered_listings`, `complex_ratings`, and `joined_listings` tables
- **Analysis**: regional stats, price distributions, correlations, interactive Altair and Matplotlib charts (histograms + KDE)
- **Price Prediction Model**: Random Forest regression pipeline
- **Streamlit Dashboard**: interactive charts, price estimator form, and critical listing evaluation via URL

## Installation & Setup

1. **Open or create a PostgreSQL database**:

   - Ensure PostgreSQL is running and you have a database ready.

2. **Configure environment variables**:

   - Copy `.env.example` (if present) to `.env` in the project root.
   - Set your database URL:
     ```ini
     DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>
     KRISHA_API_BASE=https://krisha.kz      # optional
     KRISHA_CITY=astana                     # optional
     ```

3. **Install Python dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Fetch data from Krisha.kz**:

   ```bash
   python data_fetch/krisha_scraper/krisha_fetch.py
   ```

5. **Fetch data from 2GIS**:

   ```bash
   python data_fetch/2gis_scraper/2gis_fetch.py
   ```

6. **Filter and load listings**:

   ```bash
   psql "$DATABASE_URL" -f joining_loading_tables/filter_squery.sql
   ```

7. **Join tables & clean in Jupyter**:

   - Open `joining_loading_tables/join_tables.ipynb`, run all cells to create the `joined_listings` table in your database.

8. **Launch the Streamlit app**:

   ```bash
   streamlit run streamlit_app/app.py
   ```

## Project Structure

```
LISTINGS_ANALYSIS_KRISHA_2GIS/
├── data_fetch/
│   ├── krisha_scraper/
│   │   └── krisha_fetch.py         # Krisha.kz data fetcher
│   └── 2gis_scraper/
│       └── 2gis_fetch.py           # 2GIS scraper
│
├── joining_loading_tables/
│   ├── filter_squery.sql           # raw listings filter SQL
│   └── join_tables.ipynb           # notebook to join and load tables
│
├── streamlit_app/
│   └── app.py                      # Streamlit dashboard
│
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker image definition
├── docker-compose.yml              # Compose setup (if applicable)
├── Makefile                        # common commands
└── .env                            # environment variables (not in VCS)
```

```
├── data_fetch/
│   ├── krisha_scraper/krisha_fetch.py     # Krisha data collection
│   └── 2gis_scraper/2gis_fetch.py         # 2GIS parsing
├── merge_and_load.py                      # merge tables and load to Postgres
├── streamlit_app/app.py                   # Streamlit dashboard
├── requirements.txt                       # project dependencies
└── .env                                   # environment variables
```

## Key Dependencies (see full list in `requirements.txt`)

```
streamlit>=1.0.0
pandas>=2.1.3
altair>=4.0.0
SQLAlchemy>=2.0.20
python-dotenv>=1.0.0
numpy>=1.26.2
matplotlib>=3.0.0
scipy>=1.10.0
scikit-learn>=1.0.0
selenium>=4.15.2
beautifulsoup4>=4.12.2
requests>=2.31.0
rapidfuzz>=2.15.1
```

## License

MIT ©&#x20;

