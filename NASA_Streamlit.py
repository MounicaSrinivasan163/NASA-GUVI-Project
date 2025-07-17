import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import base64
from datetime import date

# Set wide layout and title
st.set_page_config(page_title="NASA Asteroid Tracker", layout="wide")
st.title("🚀 NASA ASTEROID TRACKER 🌑🚁")

# Set background image with overlay
def set_bg_from_local(image_path):
    with open(image_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.4)), url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        color: black;
    }}
    h1, h2, h3, h4, h5, h6, .stMarkdown, .css-1v0mbdj p {{
        color: black !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Path to image
image_path = r"background.jpg"
set_bg_from_local(image_path)

# Connect to DB
def get_connection():
    return mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        user="3cv2ASCBfAqu698.root",
        password="HP2EPslJTmy95ozj",
        database="nasa_asteroid_db",
        port=4000
    )

# Predefined queries
query_dict = {
    "Select one query": None,

    "All Asteroids": """
        SELECT * FROM asteroids LIMIT 100;
    """,

    "Count of many times each asteroid has approached Earth": """
        SELECT name, COUNT(*) AS no_of_times_approached 
        FROM asteroids 
        GROUP BY name;
    """,

    "Average velocity of each asteroid over multiple approaches": """
        SELECT a.name, ROUND(AVG(c.relative_velocity_kmph), 2) AS average_velocity 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        GROUP BY a.name;
    """,

    "List top 10 fastest asteroids": """
        SELECT a.id, a.name, c.relative_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        ORDER BY c.relative_velocity_kmph DESC 
        LIMIT 10;
    """,

    "Potentially hazardous asteroids that have approached Earth more than 3 times": """
        SELECT id, name, COUNT(*) AS no_of_approaches, is_potentially_hazardous_asteroid 
        FROM asteroids 
        WHERE is_potentially_hazardous_asteroid = 1 
        GROUP BY id, name 
        HAVING no_of_approaches > 3;
    """,

    "The month with the most asteroid approaches": """
        SELECT MONTH(close_approach_date) AS approach_month, COUNT(*) AS no_of_approaches 
        FROM close_approach 
        GROUP BY approach_month 
        ORDER BY no_of_approaches DESC 
        LIMIT 1;
    """,

    "The asteroid with the fastest ever approach speed": """
        SELECT a.name, c.relative_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        ORDER BY c.relative_velocity_kmph DESC 
        LIMIT 1;
    """,

    "Sort asteroids by maximum estimated diameter (descending)": """
        SELECT name, estimated_diameter_max_km 
        FROM asteroids 
        ORDER BY estimated_diameter_max_km DESC, name;
    """,

    "An asteroid whose closest approach is getting nearer over time": """
        SELECT name, MIN(close_approach_date) AS first_date, MIN(miss_distance_km) AS min_distance_km
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        GROUP BY name
        ORDER BY min_distance_km ASC
        LIMIT 10;
    """,

    "The name of each asteroid along with the date and miss distance of its closest approach to Earth": """
        SELECT a.name, c.close_approach_date, c.miss_distance_km 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        ORDER BY a.name, c.close_approach_date ASC, c.miss_distance_km DESC;
    """,

    "List names of asteroids that approached Earth with velocity > 50,000 km/h": """
        SELECT a.name, c.relative_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        WHERE c.relative_velocity_kmph > 50000 
        ORDER BY c.relative_velocity_kmph DESC;
    """,

    "Count how many approaches happened per month": """
        SELECT MONTH(close_approach_date) AS approach_month, COUNT(*) AS no_of_approaches 
        FROM close_approach 
        GROUP BY approach_month;
    """,

    "Asteroid with the highest brightness (lowest magnitude value)": """
        SELECT name 
        FROM asteroids 
        WHERE absolute_magnitude_h = (SELECT MIN(absolute_magnitude_h) FROM asteroids);
    """,

    "Get number of hazardous vs non-hazardous asteroids": """
        SELECT 
            COUNT(CASE WHEN is_potentially_hazardous_asteroid = 0 THEN 1 END) AS non_hazardous_count,
            COUNT(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 END) AS hazardous_count  
        FROM asteroids;
    """,

    "Asteroids that passed closer than the Moon (lesser than 1 LD), along with their close approach date and distance": """
        SELECT a.name, c.close_approach_date, c.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.miss_distance_lunar < 1
        ORDER BY c.miss_distance_lunar ASC;
    """,

    "Asteroids that came within 0.05 AU(astronomical distance)": """
        SELECT a.name, c.astronomical 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        WHERE c.astronomical <= 0.05;
    """,

    "Asteroids with average diameter > 1 km": """
        SELECT name, 
               ROUND((estimated_diameter_min_km + estimated_diameter_max_km)/2, 3) AS avg_diameter_km 
        FROM asteroids 
        WHERE ((estimated_diameter_min_km + estimated_diameter_max_km)/2) > 1 
        ORDER BY avg_diameter_km DESC;
    """,

    "Top 5 most frequently approaching asteroids": """
        SELECT name, COUNT(*) AS approach_count 
        FROM asteroids 
        GROUP BY name 
        ORDER BY approach_count DESC 
        LIMIT 5;
    """,

    "Year-wise count of asteroid approaches": """
        SELECT YEAR(close_approach_date) AS year, COUNT(*) AS total_approaches 
        FROM close_approach 
        GROUP BY YEAR(close_approach_date) 
        ORDER BY year;
    """,

    "Closest approach for each asteroid": """
        SELECT a.name, MIN(c.miss_distance_km) AS closest_approach_km 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        GROUP BY a.name 
        ORDER BY closest_approach_km ASC 
        LIMIT 20;
    """,

    "Fastest approach for each asteroid": """
        SELECT a.name, MAX(c.relative_velocity_kmph) AS max_velocity_kmph 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        GROUP BY a.name 
        ORDER BY max_velocity_kmph DESC 
        LIMIT 20;
    """,

    "Average miss distance by hazardous status": """
        SELECT a.is_potentially_hazardous_asteroid, 
               ROUND(AVG(c.miss_distance_km), 2) AS avg_miss_distance_km 
        FROM asteroids a 
        JOIN close_approach c ON a.id = c.neo_reference_id 
        GROUP BY a.is_potentially_hazardous_asteroid;
    """,

    "Asteroid counts grouped by absolute magnitude": """
        SELECT 
            CASE 
                WHEN absolute_magnitude_h < 15 THEN 'Very Bright (<15)'
                WHEN absolute_magnitude_h BETWEEN 15 AND 20 THEN 'Bright (15-20)'
                WHEN absolute_magnitude_h BETWEEN 20 AND 25 THEN 'Moderate (20-25)'
                ELSE 'Dim (>25)'
            END AS magnitude_category,
            COUNT(*) AS count
        FROM asteroids
        GROUP BY magnitude_category;
    """
}


# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["About", "Query", "Filters", "Visualizations"])

# ABOUT TAB
with tab1:
    st.header("🌍 About This Project")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        This project analyzes **Near-Earth Objects (NEOs)** — asteroids and comets that come close to Earth, using data provided by **NASA's NEO API**.

        ### 📌 Purpose
        - Track and explore close-approaching asteroids  
        - Analyze velocity, distance, size, and hazard status  
        - Help raise awareness and understanding of asteroid behaviors  

        ### 🛰 Data Source
        - NASA's [Near-Earth Object Web Service (NeoWs)](https://api.nasa.gov/)  
        - Updated regularly with new asteroid observations  
        """)

    with col2:
        st.markdown("""
        ### 🔍 Key Features
        - Predefined SQL queries to explore the dataset  
        - Identify hazardous asteroids  
        - Analyze approach frequency and velocities  
        - Explore which asteroids passed closest to Earth  

        ### 👨‍💻 Tools Used
        - **Python** with **Streamlit** for the interface  
        - **MySQL** for structured data storage  
        - **Pandas** for data handling  
        - **NASA APIs** for real-world data  

        ---
        *Developed as a data science portfolio project to demonstrate real-time data analysis and web app deployment.*
        """)

# QUERY TAB
with tab2:
    st.header("SQL Queries")
    selected_query = st.selectbox("Choose a query:", list(query_dict.keys()))
    if selected_query and query_dict[selected_query]:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_dict[selected_query])
        results = cursor.fetchall()
        df = pd.DataFrame(results)
        st.session_state["query_df"] = df
        st.dataframe(df)
        cursor.close()
        conn.close()

# FILTER TAB
with tab3:
    DEFAULTS = {
        "date_range": (date(2024, 1, 1), date(2025, 2, 8)),
        "hazardous": "All",
        "magnitude": (10.0, 50.0),
        "diameter_min": (0.0, 5.0),
        "diameter_max": (0.0, 10.0),
        "velocity": (5000, 200000),
        "astro_dist": (0.0, 0.6),
        "miss_km": (150000, 75000000),
        "miss_lunar": (0.0, 200.0)
    }

    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if st.button("🔄 Reset Filters"):
        for key, val in DEFAULTS.items():
            st.session_state[key] = val
        st.experimental_rerun() 

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    with st.form("filter_form"):
        st.markdown("### 🧪 Filter Asteroid Data")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.session_state["magnitude"] = st.slider("🔆 Absolute Magnitude (H)", 10.0, 50.0, value=st.session_state["magnitude"])
            st.session_state["diameter_min"] = st.slider("📏 Min Diameter (km)", 0.0, 5.0, value=st.session_state["diameter_min"])
            st.session_state["diameter_max"] = st.slider("📏 Max Diameter (km)", 0.0, 10.0, value=st.session_state["diameter_max"])

        with col2:
            st.session_state["velocity"] = st.slider("🚀 Velocity (kmph)", 5000, 200000, value=st.session_state["velocity"])
            st.session_state["astro_dist"] = st.slider("🌌 Astronomical Unit", 0.0, 0.6, value=st.session_state["astro_dist"])
            st.session_state["miss_km"] = st.slider("🪐 Miss Distance (km)", 5000, 80000000, value=st.session_state["miss_km"])

        with col3:
            st.session_state["miss_lunar"] = st.slider("🌗 Miss Distance (Lunar)", 0.0, 200.0, value=st.session_state["miss_lunar"])
            st.session_state["date_range"] = st.date_input("🗕️ Date Range", value=st.session_state["date_range"])
            st.session_state["hazardous"] = st.selectbox("☢️ Hazardous?", ["All", "Yes", "No"],
                index=["All", "Yes", "No"].index(st.session_state["hazardous"]))

        submit = st.form_submit_button("🔍 Apply Filters")

    if submit:
        query = """
        SELECT a.name, a.absolute_magnitude_h, a.estimated_diameter_min_km, a.estimated_diameter_max_km,
               a.is_potentially_hazardous_asteroid, c.close_approach_date, c.relative_velocity_kmph,
               c.miss_distance_km, c.miss_distance_lunar, c.astronomical
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE 1=1
        """
        params = []

        if st.session_state["hazardous"] == "Yes":
            query += " AND a.is_potentially_hazardous_asteroid = 1"
        elif st.session_state["hazardous"] == "No":
            query += " AND a.is_potentially_hazardous_asteroid = 0"

        query += " AND a.absolute_magnitude_h BETWEEN %s AND %s"
        params.extend(st.session_state["magnitude"])
        query += " AND a.estimated_diameter_min_km BETWEEN %s AND %s"
        params.extend(st.session_state["diameter_min"])
        query += " AND a.estimated_diameter_max_km BETWEEN %s AND %s"
        params.extend(st.session_state["diameter_max"])
        query += " AND c.close_approach_date BETWEEN %s AND %s"
        d1, d2 = st.session_state["date_range"]
        params.extend([d1, d2])
        query += " AND c.relative_velocity_kmph BETWEEN %s AND %s"
        params.extend(st.session_state["velocity"])
        query += " AND c.astronomical BETWEEN %s AND %s"
        params.extend(st.session_state["astro_dist"])
        query += " AND c.miss_distance_km BETWEEN %s AND %s"
        params.extend(st.session_state["miss_km"])
        query += " AND c.miss_distance_lunar BETWEEN %s AND %s"
        params.extend(st.session_state["miss_lunar"])

        cursor.execute(query, params)
        filtered_df = pd.DataFrame(cursor.fetchall())
        st.session_state["filtered_df"] = filtered_df

        if filtered_df.empty:
            st.warning("⚠️ No results found.")
        else:
            st.success(f"✅ Found {len(filtered_df)} results.")
            st.dataframe(filtered_df, use_container_width=True)

        cursor.close()
        conn.close()

with tab4:
    st.header("📊 Visualizations Based on Filtered Data")

    if "filtered_df" in st.session_state and not st.session_state["filtered_df"].empty:
        viz_df = st.session_state["filtered_df"]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📅 Approaches Over Time")
            viz_df["close_approach_date"] = pd.to_datetime(viz_df["close_approach_date"])
            viz_df["month"] = viz_df["close_approach_date"].dt.to_period("M").astype(str)

            monthly_counts = viz_df.groupby("month").size().reset_index(name="approach_count")

            fig1 = px.line(
                monthly_counts,
                x="month",
                y="approach_count",
                title="Number of Asteroid Approaches Over Time",
                labels={"month": "Month", "approach_count": "Number of Approaches"}
            )
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)

        with col1:
            st.subheader("📏 Estimated Diameter vs. Velocity")
            fig2 = px.scatter(viz_df,
                             x="estimated_diameter_max_km",
                             y="relative_velocity_kmph",
                             color="is_potentially_hazardous_asteroid",
                             labels={"estimated_diameter_max_km": "Max Diameter (km)",
                                     "relative_velocity_kmph": "Velocity (kmph)",
                                     "is_potentially_hazardous_asteroid": "Hazardous"},
                             title="Velocity vs. Diameter (Colored by Hazard)")
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.subheader("🪐 Hazardous vs Non-Hazardous Count")
            hazard_counts = viz_df["is_potentially_hazardous_asteroid"].value_counts().reset_index()
            hazard_counts.columns = ["Hazardous", "Count"]
            hazard_counts["Hazardous"] = hazard_counts["Hazardous"].map({0: "Non-Hazardous", 1: "Hazardous"})

            fig3 = px.bar(
                hazard_counts,
                x="Hazardous",
                y="Count",
                color="Hazardous",
                title="Count of Hazardous vs Non-Hazardous Asteroids"
            )
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.subheader("🪐 Miss Distance (km) vs. Velocity")
            fig4 = px.scatter(viz_df,
                              x="miss_distance_km",
                              y="relative_velocity_kmph",
                              title="Miss Distance vs. Velocity")
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("⚠️ No filtered data found. Please apply filters in Tab 3.")




