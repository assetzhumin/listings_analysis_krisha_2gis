#!/usr/bin/env python3
import os, sys, time, requests, pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Load .env ──────────────────────────────────────────────────────────────────────
load_dotenv()  # expects DATABASE_URL, optional KRISHA_API_BASE & KRISHA_CITY

# ─── Configuration ──────────────────────────────────────────────────────────────────
API_BASE  = os.getenv("KRISHA_API_BASE", "https://krisha.kz")
CITY      = os.getenv("KRISHA_CITY", "astana")
BASE_URL  = f"{API_BASE}/prodazha/kvartiry/{CITY}/"
PARAMS    = {"has_photo": 1}
MAX_PAGES = 100   # <- SET HOW MANY PAGES YOU WANT TO FETCH

# ─── HTTP session w/ retries & headers ─────────────────────────────────────────────
session = requests.Session()
retry = Retry(total=5, backoff_factor=1, status_forcelist=[429,500,502,503,504], allowed_methods=["GET"])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8"
})

def fetch_all():
    items = []
    for page in range(1, MAX_PAGES + 1):
        try:
            resp = session.get(BASE_URL, params={**PARAMS, "page": page}, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[WARN] page {page} failed: {e}")
            time.sleep(2)
            continue

        # dump HTML for inspection on first page
        if page == 1:
            with open("page1.html", "w", encoding="utf-8") as f:
                f.write(resp.text)

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("div.a-card__inc")
        if not cards:
            print("No more listings found, stopping.")
            break

        for card in cards:
            a_img = card.select_one("a.a-card__image")
            href  = a_img["href"] if a_img else None
            link  = (API_BASE + href) if href and href.startswith("/") else href

            descr = card.select_one("div.a-card__descr")
            details = descr.get_text(" | ", strip=True) if descr else None

            items.append({"details": details, "link": link})

        print(f"Page {page} → collected {len(items)} listings so far")
        time.sleep(1.5)
    return items

def to_dataframe(items):
    if not items:
        print("No items — exiting.")
        return pd.DataFrame()
    df = pd.DataFrame(items)
    print("Columns:", df.columns.tolist())
    return df[["details", "link"]]

def save_to_postgres(df):
    url = os.getenv("DATABASE_URL") or sys.exit("Set DATABASE_URL in .env")
    engine = create_engine(url)
    df.to_sql("listings", engine, if_exists="replace", index=False)
    print(f"✅ Saved {len(df)} rows to PostgreSQL")

if __name__ == "__main__":
    print("Starting scrape…")
    items = fetch_all()
