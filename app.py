import streamlit as st
import sqlite3
import polars as pl
import plotly.express as px

# Путь к БД
DB_PATH = "/opt/airflow/project/data/weather.db"


@st.cache_data
def load_data():
    """Загрузка данных из SQLite"""
    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT *
    FROM weather
    """

    df = pl.read_database(query=query, connection=conn)
    conn.close()

    return df


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ Аналитика погоды")
st.write("Исторические данные и прогноз по городам")

# Загрузка данных
df = load_data()

if df.is_empty():
    st.warning("Нет данных в базе weather.db")
    st.stop()

# Получаем список городов
cities = sorted(df["city"].unique().to_list())

selected_city = st.selectbox(
    "Выберите город",
    cities
)

# Фильтрация
city_data = df.filter(
    pl.col("city") == selected_city
).sort("date")

if city_data.is_empty():
    st.warning("Нет данных по выбранному городу")
    st.stop()

# --------------------------------
# График температуры
# --------------------------------
fig_temp = px.line(
    city_data.to_pandas(),
    x="date",
    y="avg_temp",
    title=f"Средняя температура в {selected_city}",
    labels={
        "avg_temp": "Температура (°C)",
        "date": "Дата"
    }
)

st.plotly_chart(fig_temp, use_container_width=True)

# --------------------------------
# График индекса комфорта
# --------------------------------
if "comfort_index" in city_data.columns:
    fig_comfort = px.line(
        city_data.to_pandas(),
        x="date",
        y="comfort_index",
        title=f"Индекс комфорта в {selected_city} (чем выше — тем комфортнее)",
        labels={
            "comfort_index": "Индекс комфорта",
            "date": "Дата"
        },
        color_discrete_sequence=["#1f77b4"]
    )

    st.plotly_chart(fig_comfort, use_container_width=True)

# --------------------------------
# Статистика
# --------------------------------
rainy_days = city_data["is_rainy"].sum()
avg_temp = city_data["avg_temp"].mean()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Средняя температура",
    f"{avg_temp:.1f}°C"
)

col2.metric(
    "Дождливых дней",
    int(rainy_days)
)

if "comfort_index" in city_data.columns:
    avg_comfort = city_data["comfort_index"].mean()

    col3.metric(
        "Средний комфорт",
        f"{avg_comfort:.1f}"
    )

# --------------------------------
# Таблица последних данных
# --------------------------------
st.subheader("Последние данные")

st.dataframe(
    city_data.tail(10).to_pandas(),
    use_container_width=True
)