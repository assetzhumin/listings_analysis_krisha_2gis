import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import os
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from math import log

load_dotenv()
db_url = os.getenv("DATABASE_URL")

@st.cache_data
def load_data():
    try:
        engine = create_engine(db_url)
        return pd.read_sql("SELECT * FROM joined_listings", engine)
    except Exception:
        # Fallback to CSV in your repo
        return pd.read_csv("data/merged_listings_with_ratings.csv")

df = load_data()
st.title("Аналитика недвижимости по обьявлениям krisha.kz")
filtered = df.copy()

prices = filtered['price_kzt'].dropna()
prices = prices[(prices > 0) & (filtered['price_kzt'] <= 150_000_000)] / 1e6

mean_price = prices.mean()
median_price = prices.median()
plt.figure(figsize=(12, 6))

n_bins = 20
counts, bins, patches = plt.hist(
    prices, bins=n_bins, alpha=0.6, edgecolor='black', color='#ffcc66'
)

kde = gaussian_kde(prices)
x = np.linspace(prices.min(), prices.max(), 500)
scale = len(prices) * (bins[1] - bins[0])
plt.plot(x, kde(x) * scale, color='blue', linewidth=2)

plt.axvline(mean_price, color='red', linestyle='--', linewidth=2, label=f'Средняя: {mean_price:.1f} млн')
plt.axvline(median_price, color='green', linestyle='--', linewidth=2, label=f'Медиана: {median_price:.1f} млн')

plt.xlabel('Цена (млн ₸)')
plt.ylabel('Количество объявлений')
plt.title('Распределение цен на квартиры (в млн ₸)')
plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()
st.pyplot(plt)

st.header("Средняя цена по районам")
avg_price = filtered.groupby('region')['price_kzt'].mean().reset_index()
chart2 = alt.Chart(avg_price).mark_bar().encode(
    x=alt.X('region:O', sort='-y'),
    y='price_kzt:Q',
    tooltip=['region', 'price_kzt']
)
st.altair_chart(chart2, use_container_width=True)

st.header("Цена по отношению к площади квартиры")
chart3 = alt.Chart(filtered).mark_circle(size=60).encode(
    x='area_m2:Q',
    y='price_kzt:Q',
    color='rooms:O',
    tooltip=['area_m2', 'price_kzt', 'rooms']
)
st.altair_chart(chart3, use_container_width=True)

st.header("Оценка цены по параметрам")

@st.cache_resource
def train_model(df):

    df2 = df.dropna(subset=["price_kzt"])
    X = df2[["rooms","area_m2","floor","year_built","region"]]
    y = df2["price_kzt"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    numeric_feats = ["rooms","area_m2","floor","year_built"]
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_feats = ["region"]
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="не указано")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, numeric_feats),
        ("cat", categorical_pipe, categorical_feats)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    model.fit(X_train, y_train)
    return model

model = train_model(df)

with st.form("price_estimator"):
    st.subheader("Введите параметры квартиры")
    rooms_in       = st.number_input("Кол-во комнат", min_value=1, max_value=10, value=2)
    area_in        = st.number_input("Площадь (м²)", min_value=10.0, max_value=1000.0, value=50.0)
    floor_in       = st.number_input("Этаж", min_value=1, max_value=100, value=5)
    year_in        = st.number_input("Год постройки", min_value=1900, max_value=2030, value=2015)
    region_in      = st.selectbox("Район", options=sorted(df["region"].unique()), index=0)

    submitted = st.form_submit_button("Оценить")
    if submitted:
        X_new = pd.DataFrame([{
            "rooms": rooms_in,
            "area_m2": area_in,
            "floor": floor_in,
            "year_built": year_in,
            "region": region_in,
        }])
        pred = model.predict(X_new)[0]
        st.success(f"Приблизительная цена: {pred:,.0f} ₸")

# st.header("Критическая оценка отдельного объявления")
# url_in = st.text_input("Вставьте URL объявления krisha.kz:")
# if st.button("Оценить объявление") and url_in:
#     rec = filtered[filtered['link'] == url_in]
#     if rec.empty:
#         st.error("Объявление не найдено в базе данных. Попробуйте вставить другую ссылку!")
#     else:
#         rec = rec.iloc[0]
#         region_df = filtered[filtered['region'] == rec['region']]

#         p_min, p_max = region_df['price_kzt'].min(), region_df['price_kzt'].max()
#         y_min, y_max = region_df['year_built'].min(), region_df['year_built'].max()
#         apr = region_df['area_m2'] / region_df['rooms']
#         apr_min, apr_max = apr.min(), apr.max()
#         f_min, f_max = region_df['floor'].min(), region_df['floor'].max()

#         def norm(val, vmin, vmax, use_log=False):
#             if pd.isna(val) or vmax <= vmin:
#                 return None
#             if use_log:
#                 val, vmin, vmax = log(val), log(vmin), log(vmax)
#             return 10 * (val - vmin) / (vmax - vmin)

#         price_score  = norm(rec['price_kzt'],    p_min,  p_max,  use_log=True)
#         year_score   = norm(rec['year_built'],   y_min,  y_max,  use_log=False)
#         area_score   = norm(rec['area_m2']/rec['rooms'], apr_min, apr_max, use_log=True)
#         floor_score  = norm(rec.get('floor', None), f_min, f_max,  use_log=False)
#         rating_score = norm(rec.get('rating_2gis', None),0, 5, use_log=False)

#         scores = {
#             'Price':        price_score,
#             'YearBuilt':    year_score,
#             'AreaPerRoom':  area_score,
#             'Floor':        floor_score,
#             '2GISRating':   rating_score
#         }

#         valid_scores = [v for v in scores.values() if v is not None]
#         overall = sum(valid_scores) / len(valid_scores) if valid_scores else None

#         st.write("### Подробные оценки по факторам:")
#         for factor, score in scores.items():
#             if score is not None:
#                 st.write(f"- {factor}: {score:.1f}/10")
#             else:
#                 st.write(f"- {factor}: —")

#         if overall is not None:
#             st.write(f"### Общая критическая оценка: **{overall:.1f}/10**")
#         else:
#             st.write("Невозможно рассчитать общую оценку — недостаточно данных.")


# RUN streamlit_app/app.py
