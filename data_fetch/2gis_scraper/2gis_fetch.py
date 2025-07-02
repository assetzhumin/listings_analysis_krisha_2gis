import os, time, csv
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine

# ─── Config ──────────────────────────────────────────────────────────────────────
MARKUP_FILENAME   = 'html-markup.txt'
CSV_DATA_FILENAME = 'complex_ratings.csv'
CITY_NAME         = 'astana'
SEARCH            = 'ЖК'
URL               = f'https://2gis.ru/{CITY_NAME}/search/{SEARCH}?m'

# ─── Prepare CSV ─────────────────────────────────────────────────────────────────
HEADERS = ['residential_complex', 'rating']
with open(CSV_DATA_FILENAME, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()

def data_handler(page_number):
    with open(MARKUP_FILENAME, 'r', encoding='utf-8') as f:
        contents = f.read()
    doc = BeautifulSoup(contents, 'html.parser')
    cards = doc.find_all('div', class_='_1kf6gff')
    rows = []
    for c in cards:
        # residential complex name
        complex_el = c.select_one('span._lvwrwt > span')
        name = complex_el.get_text(strip=True) if complex_el else 'не указано'
        # rating
        rating_el = c.find('div', class_='_y10azs')
        rating = rating_el.get_text(strip=True) if rating_el else 'null'
        rows.append({'residential_complex': name, 'rating': rating})
    with open(CSV_DATA_FILENAME, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        for row in rows:
            writer.writerow(row)
    print(f'Finished page {page_number}')

# ─── Scrape ──────────────────────────────────────────────────────────────────────
browser = webdriver.Chrome()
browser.maximize_window()
browser.get(URL)
browser.implicitly_wait(10)

# find total pages
page_el = browser.find_element(By.XPATH, "(//span[@class='_1xhlznaa'])[1]")
num_pages = int(page_el.text)//12 + 3

try:
    scroll = browser.find_element(By.XPATH, "(//div[@class='_15gu4wr'])[last()]")
    for page in range(1, num_pages+1):
        with open(MARKUP_FILENAME, 'w', encoding='utf-8') as f:
            f.write(browser.page_source)
        data_handler(page)
        browser.execute_script("arguments[0].scrollIntoView(false);", scroll)
        time.sleep(1)
        browser.find_element(By.XPATH, "//div[@class='_5ocwns']//div[2]").click()
        time.sleep(2)
except Exception:
    pass
finally:
    browser.quit()

# ─── Load to DB ──────────────────────────────────────────────────────────────────
load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL not set in .env")
df = pd.read_csv(CSV_DATA_FILENAME)
engine = create_engine(db_url)
df.to_sql('complex_ratings', engine, if_exists='replace', index=False)
print(f"✅ Wrote {len(df)} rows to complex_ratings"); 


# RUN this script USING the command below, then run the load_data.py to load it into the databse

# -----------------------------------------
# git clone https://github.com/<YOUR-USERNAME>/LISTINGS_ANALYSIS_KRISHA_2GIS.git
# cd LISTINGS_ANALYSIS_KRISHA_2GIS
# pip install -r requirements.txt
#    Linux / MacOS:
# python3 -m venv venv
# source venv/bin/activate
#    Windows (Powershell):
# venv\Scripts\Activate.ps1
# python data_fetch/2gis_scraper/2gis_fetch.py
# -----------------------------------------

# Note: Make sure to have the ChromeDriver installed and its path set in your environment variables.
# You can download it from https://chromedriver.chromium.org/downloads
# Ensure that the version of ChromeDriver matches your installed version of Chrome. 
