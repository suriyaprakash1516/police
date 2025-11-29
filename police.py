import streamlit as st
import pandas as pd
import pymysql 
import plotly.express as px

# database connection
def create_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="Surya@1516",
            database='securecheck',
            cursorclass=pymysql.cursors.DictCursor
    )
        return connection
    except Exception as e:
        st.error(f"Database connection Error:{e}")
        return None

# Fetch data from database
def fetch_data(query):
    connection =  create_connection()
    if connection:
        try: 
            with connection.cursor() as cursor:
                cursor.execute(query) 
                result=cursor.fetchall()
                df=pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    
# Streamlit UI
st.set_page_config(page_title="Securecheck Police Dashboard",layout="wide")

st.title("🚨:Securecheck Police Check Post Digital Ledger")
st.markdown("Real-time monitoring and insigts for law enforcement🚓")

# show full table
st.header("Police Logs Overview📋")
query="SELECT * FROM police_logs"
data=fetch_data(query)
st.dataframe(data,use_container_width=True)

# Quick metrics
st.header("📊key metrics")
col1,col2,col3,col4 = st.columns(4)

with col1:
    total_stops = data.shape[0]
st.metric("Total Police Stops",total_stops)

with col2:
    arrests=data[data['stop_outcome'].str.contains("arrest",case=False,na=False)].shape[0]
    st.metric("Total Arrests",arrests)

with col3:
     warning=data[data['stop_outcome'].str.contains("warning",case=False,na=False)].shape[0]
     st.metric("Total warnings",warning)

with col4:
     drug_related=data[data['drugs_related_stop']==1].shape[0]
     st.metric("Drugs Related Stop",drug_related)

# Chats
st.header("📈Visual Insights")
tab1,tab2 =st.tabs(["stops by violation","Driver gender Distribution"])

with tab1:
    if not data.empty and 'violation'in data.columns:
        violation_data=data['violation'].value_counts().reset_index()
        violation_data.columns=['violation','count']
        fig = px.bar(violation_data,x='violation',y='count',title="Stops by Violation Type",color='violation')
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning("No data available for Violation chart.")


with tab2:
    if not data.empty and 'driver_gender'in data.columns:
        gender_data=data['driver_gender'].value_counts().reset_index()
        gender_data.columns=['Gender','count']
        fig = px.bar(gender_data,x ='Gender',y ='count',title="Driver Gender Distribution",color='Gender')
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning("No data available for Driver Gender chart.")

# Advanced Queries

st.header("🧩Advanced Insights")

selected_query=st.selectbox("select a Query to run",[
    # Medium Level
    "Top 10 Vehicles involved in drug-related stops",
    "Most frequently searched vehicles",
    "Driver age group with highest arrest rate",
    "Gender distribution of drivers stopped in each country",
    "Race + gender combination with highest search rate",
    "Time of day with most traffic stops",
    "Average stop duration for different violations",
    "Night-time stops more likely to lead to arrests?",
    "Violations associated with searches or arrests",
    "Common violations among younger drivers (<25)",
    "Violations that rarely result in search or arrest",
    "Countries with highest drug-related stops",
    "Arrest rate by country and violation",
    "Countries with the most stops involving a search",

    # Complex Level
    "Yearly breakdown of stops & arrests by country",
    "Driver violation trends by age & race",
    "Time period analysis (Year, Month, Hour)",
    "Violations with high search & arrest rates",
    "Driver demographics by country",
    "Top 5 violations with highest arrest rates"
]) 

query_map={
    # Medium Queries
    "Top 10 Vehicles involved in drug-related stops":
        """SELECT vehicle_number, COUNT(*) AS drug_cases
           FROM traffic_stops
           WHERE drugs_related_stop='True'
           GROUP BY vehicle_number
           ORDER BY drug_cases DESC LIMIT 10;""",

    "Most frequently searched vehicles":
        """SELECT vehicle_number, COUNT(*) AS searches
           FROM traffic_stops WHERE search_conducted='True'
           GROUP BY vehicle_number ORDER BY searches DESC;""",

    "Driver age group with highest arrest rate":
        """SELECT driver_age, AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY driver_age ORDER BY arrest_rate DESC;""",

    "Gender distribution of drivers stopped in each country":
        """SELECT country_name, driver_gender, COUNT(*) AS total
           FROM traffic_stops GROUP BY country_name, driver_gender;""",

    "Race + gender combination with highest search rate":
        """SELECT driver_race, driver_gender,
                  AVG(search_conducted='True')*100 AS search_rate
           FROM traffic_stops GROUP BY driver_race, driver_gender
           ORDER BY search_rate DESC;""",

    "Time of day with most traffic stops":
        """SELECT substr(stop_time, 1, 2) AS hour,
                  COUNT(*) AS total FROM traffic_stops
           GROUP BY hour ORDER BY total DESC;""",

    "Average stop duration for different violations":
        """SELECT violation,
                  AVG(CASE stop_duration
                      WHEN '<5 min' THEN 3
                      WHEN '6-15 min' THEN 10
                      WHEN '16-30 min' THEN 20
                  END) AS avg_minutes
           FROM traffic_stops GROUP BY violation;""",

    "Night-time stops more likely to lead to arrests?":
        """SELECT
            CASE
              WHEN CAST(substr(stop_time,1,2) AS INT) BETWEEN 20 AND 23 OR
                   CAST(substr(stop_time,1,2) AS INT) BETWEEN 0 AND 4
              THEN 'Night' ELSE 'Day' END AS period,
              AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY period;""",

    "Violations associated with searches or arrests":
        """SELECT violation,
                  AVG(search_conducted='True')*100 AS search_rate,
                  AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY violation;""",

    "Common violations among younger drivers (<25)":
        """SELECT violation, COUNT(*) AS total
           FROM traffic_stops WHERE driver_age < 25
           GROUP BY violation ORDER BY total DESC;""",

    "Violations that rarely result in search or arrest":
        """SELECT violation,
                  AVG(search_conducted='True')*100 AS search_rate,
                  AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY violation
           HAVING search_rate < 5 AND arrest_rate < 2;""",

    "Countries with highest drug-related stops":
        """SELECT country_name, SUM(drugs_related_stop='True') AS total
           FROM traffic_stops GROUP BY country_name
           ORDER BY total DESC;""",

    "Arrest rate by country and violation":
        """SELECT country_name, violation,
                  AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY country_name, violation
           ORDER BY arrest_rate DESC;""",

    "Countries with the most stops involving a search":
        """SELECT country_name,
                  SUM(search_conducted='True') AS searches
           FROM traffic_stops GROUP BY country_name
           ORDER BY searches DESC;""",

    # Complex Queries
    "Yearly breakdown of stops & arrests by country":
        """SELECT country_name,
                  substr(stop_date,1,4) AS year,
                  COUNT(*) AS stops,
                  SUM(is_arrested) AS arrests
           FROM traffic_stops GROUP BY country_name, year;""",

    "Driver violation trends by age & race":
        """SELECT driver_age, driver_race, violation, COUNT(*) AS total
           FROM traffic_stops GROUP BY driver_age, driver_race, violation;""",

    "Time period analysis (Year, Month, Hour)":
        """SELECT substr(stop_date,1,4) AS year,
                  substr(stop_date,6,2) AS month,
                  substr(stop_time,1,2) AS hour,
                  COUNT(*) AS total
           FROM traffic_stops GROUP BY year, month, hour;""",

    "Violations with high search & arrest rates":
        """SELECT violation,
                  AVG(search_conducted='True')*100 AS search_rate,
                  AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY violation
           ORDER BY arrest_rate DESC;""",

    "Driver demographics by country":
        """SELECT country_name, driver_age, driver_gender, driver_race,
                  COUNT(*) AS total
           FROM traffic_stops
           GROUP BY country_name, driver_age, driver_gender, driver_race;""",

    "Top 5 violations with highest arrest rates":
        """SELECT violation, AVG(is_arrested)*100 AS arrest_rate
           FROM traffic_stops GROUP BY violation
           ORDER BY arrest_rate DESC LIMIT 5;"""
}

if st.button("Run SQL Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.write(result)
    else:
        st.warning("No results Found for the Selected Query.")

st.markdown("---")
st.markdown("Built with ❤️ for Law Enforement by secureCheck")
st.header("🔍Custom Natural Language Filter")


st.markdown("Fill in the details below to get a natural language prediction of the stop outcome based on the existing data.")


st.header("📝 Add New Police log & predict outcome and Violation")

# Input form for all fields(excluding outputs) 
with st.form("new_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["Male", "Female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Was a search Conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"])
    stop_duration = st.selectbox("Stop Duration", data['stop_duration'].dropna().unique())
    vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Predict Stop Outcome & Violation")

    # RUN PREDICTION HERE
    if submitted:

        # Filter data for prediction
        filtered_data = data[
            (data['driver_gender'] == driver_gender) &
            (data['driver_age'] == driver_age) &
            (data['search_conducted'].astype(str) == search_conducted) &
            (data['stop_duration'] == stop_duration) &
            (data['drugs_related_stop'].astype(str) == drugs_related_stop)
        ]

        # Predict stop_outcome
        if not filtered_data.empty:
            predicted_outcome = filtered_data['stop_outcome'].mode()[0]
            predicted_violation = filtered_data['violation'].mode()[0]
        else:
            predicted_outcome = "warning"   # fallback
            predicted_violation = "speeding"

        # Natural-language summary
        search_text = "A search was conducted" if search_conducted == "1" else "No search was conducted"
        drug_text = "was drug-related" if drugs_related_stop == "1" else "was not drug-related"

        st.markdown(f""" 
        ### 🚔 **Prediction Summary**
        
        - **Predicted Violation:** {predicted_violation}
        - **Predicted Stop Outcome:** {predicted_outcome}

        📃 A {driver_age}-year-old **{driver_gender}** driver in **{country_name}**  
        was stopped at **{stop_time.strftime('%I:%M %p')}** on **{stop_date}**.  
        {search_text}, and the stop {drug_text}.  
        Stop duration: **{stop_duration}**  
        Vehicle number: **{vehicle_number}**
        """)
