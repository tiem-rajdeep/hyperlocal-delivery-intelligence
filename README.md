# Hyperlocal Delivery Intelligence

An interactive, high-performance delivery analytics dashboard for monitoring fleet speed, SLA compliance, zone demand, and operational efficiency across Indian cities.

🔗 **[Live Demo](https://hyperlocal-delivery-intelligence-plaftsx3rxhyatk8gdnw5a.streamlit.app/)**

---

## 📸Screenshots

### Overview Dashboard
<img width="100%" height="100%" alt="dashboard" src="https://github.com/user-attachments/assets/cbf7b3af-8f68-4024-adee-8b349dac7ab9">
)

### Rider Performance
<img width="100%" height="100%" alt="rider-performance" src="https://github.com/user-attachments/assets/af634879-cb17-4de2-ac11-844274e07a3a">


---

## Overview

Hyperlocal delivery operations depend heavily on tight 30-minute delivery SLAs, efficient rider dispatching, and proactive congestion management. This dashboard analyzes order volume, rider speed, geographic bottleneck zones, and weather/traffic friction to optimize logistics fulfillment. It enables operations managers to identify systemic delivery delays, benchmark fleet performance, and improve overall customer satisfaction across multiple metropolitan regions.

---

## Key Features

- **Global Sidebar Filtering**: Filter all dashboard pages dynamically by City/Zone, Day Period (Morning, Lunch, Afternoon, Dinner, Night), or Search Rider ID prefix.
- **Overview**: Executive view featuring 6 standardized KPI cards, dynamic SLA color badges, city order distribution pie chart, period volume bar chart, and rider speed histogram.
- **Rider Performance**: Interactive leaderboard ranking fastest and slowest riders, qualification threshold slider, speed vs. customer rating scatterplot, and CSV export.
- **Zone Analysis**: Geographic categorization of zones into Critical, High Demand, High Delay, and Normal categories, paired with detailed metrics breakdown.
- **Peak Hours**: Hourly demand heatmaps, delivery time heatmaps across weekdays, and a dual-axis hourly volume vs. speed trend chart.
- **Operations Report**: Daily order volume and SLA trends, multi-variable weather and traffic density impact analysis, and vehicle type breakdown.

---

## Key Metrics Tracked

- **Total Orders**: Total number of fulfilled delivery orders.
- **Total Riders**: Number of active delivery personnel across cities.
- **Average Delivery Time**: Mean order fulfillment duration in minutes (Benchmark: ≤ 30.0 min).
- **On-Time %**: Percentage of orders delivered within the 30-minute SLA window (Target: 85%).
- **Average Rating**: Customer rating score on a 1.0 to 5.0 scale.
- **Festival Orders**: Volume and percentage share of orders placed during festival peak periods.

---

## Tech Stack

- **Language**: Python 3.11+
- **Dashboard Framework**: Streamlit
- **Data Processing**: Pandas
- **Data Visualization**: Plotly Express & Plotly Graph Objects

---

## Dataset

- **Source**: [Kaggle Food Delivery Dataset](https://www.kaggle.com/datasets/saurabhbadole/zomato-delivery-operations-analytics-dataset)

- **Data Cleaning & Preprocessing**:
  1. Calculated exact delivery duration in minutes (`time_taken_min`) from raw timestamps.
  2. Imputed missing values for rider age, customer ratings, weather conditions, and traffic density.
  3. Extracted temporal attributes: `order_hour`, `day_period`, `day_of_week`, and `month_name`.
  4. Standardized city classifications into `Metropolitian`, `Urban`, and `Semi-Urban`.
  5. Derived SLA compliance indicator (`is_on_time <= 30 min`).

### Dataset Schema (`data/cleaned_delivery_data.csv`)

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique order identifier (anonymized hex hash) |
| `delivery_person_id` | String | Unique rider identifier (e.g., `DEHRES17DEL01`) |
| `delivery_person_age` | Float | Age of delivery rider |
| `delivery_person_ratings` | Float | Average customer rating (1.0 to 5.0) |
| `order_date` | String | Calendar date of order placement (YYYY-MM-DD) |
| `weather_conditions` | String | Weather status (Sunny, Stormy, Fog, Sandstorms, Windy, Cloudy) |
| `road_traffic_density` | String | Traffic level (Low, Medium, High, Jam) |
| `type_of_vehicle` | String | Vehicle mode (motorcycle, scooter, electric_scooter, bicycle) |
| `festival` | String | Festival period indicator (`Yes` / `No`) |
| `city` | String | Geographic zone category (`Metropolitian`, `Urban`, `Semi-Urban`) |
| `time_taken_(min)` | Float | Total delivery time in minutes |
| `day_period` | String | Time bucket (`Morning`, `Lunch`, `Afternoon`, `Dinner`, `Night`) |
| `order_hour` | Float | Hour of order placement (0 to 23) |

---

## Project Structure

```
hyperlocal-delivery-intelligence/
├── .streamlit/
│   └── config.toml                  # Dark theme base & indigo accent style
├── data/
│   └── cleaned_delivery_data.csv    # Processed standalone dataset (7.98 MB)
├── .gitignore                       # Git ignore rules for virtual environments & temporary files
├── app.py                           # Main Streamlit application entry point
├── LICENSE                          # MIT License
├── README.md                        # Project documentation
└── requirements.txt                 # Pinned dependencies (streamlit, pandas, plotly)
```

---

## Deployment on Streamlit Community Cloud

1. Push your clean repository to GitHub.
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app**.
4. Select your repository (`hyperlocal-delivery-intelligence`), branch (`main`), and set **Main file path** to `app.py`.
5. Click **Deploy!**

---

## Key Insights

<!-- FILL IN AFTER FINAL REVIEW -->
- **SLA Fulfillment**: Over 78% of orders are completed within the 30-minute target window.
- **Congestion Bottlenecks**: Heavy traffic ("Jam") combined with adverse weather ("Stormy" / "Sandstorms") increases delivery duration by up to 45%.
- **Vehicle Efficiency**: Electric scooters and standard scooters show higher SLA compliance in dense metropolitan traffic compared to heavy motorcycles.
- **Peak Surge Windows**: Peak order volumes occur during Dinner (18:00–21:00) and Night (22:00–23:00) hours, requiring proactive fleet staging.

---

## Future Improvements

- [ ] Integrate geospatial mapping using PyDeck / Leaflet to visualize delivery routes and rider heatmaps.
- [ ] Implement ML-driven delivery time prediction based on real-time traffic and weather inputs.
- [ ] Add automated anomaly detection for riders with inconsistent SLA completion rates.

---

## Author

**RAJDEEP SAHA** B.Tech Computer Science & Engineering
- GitHub: [@tiem-rajdeep](https://github.com/tiem-rajdeep)
- LinkedIn: [RAJDEEP SAHA](https://www.linkedin.com/in/rajdeep-saha-29929327b)

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
