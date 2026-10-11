# 🚀 Text-to-SQL & Visual Analytics with Sarvam AI and MySQL

An end-to-end AI-powered Business Intelligence & Data Analytics application that allows you to ask questions in plain English (or Indic languages), converts them into optimized MySQL queries using **Sarvam AI**, executes them securely, and dynamically renders interactive charts (**Plotly**) and tabular summaries (**Streamlit**).

---

## 🌟 Key Features

1. **Natural Language to SQL**:
   - Translates conversational queries into valid MySQL `SELECT` queries using **Sarvam AI** (e.g. `sarvam-105b`).
   - Automatically injects live MySQL schema context (tables, columns, types, foreign keys) so the model never hallucinates table names.

2. **Automated Visual Analytics (Pictorial Representation)**:
   - Evaluates data shape and data types dynamically.
   - Automatically plots:
     - **Bar / Column Charts**: for categorical metrics (e.g. sales by category, revenue by city).
     - **Line / Trend Charts**: for time-series and date-based trends (e.g. monthly revenue).
     - **Donut / Pie Charts**: for share and distribution (e.g. payment methods, order status).
     - **KPI Indicator Cards**: for aggregate values (e.g. total revenue, total customers).
     - **Scatter Plots**: for correlations.

3. **Read-Only Security Guardrails**:
   - Queries are validated prior to execution.
   - Any destructive DDL or DML statements (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`) are strictly blocked.

4. **One-Click Dummy Database Seeder**:
   - Includes a realistic E-Commerce and Retail Analytics dataset:
     - `customers`: 100 customer profiles with segments, Indian cities & contact details.
     - `categories`: 6 product categories (Electronics, Fashion, Appliances, Sports, etc.).
     - `products`: 26 catalog items with costs, selling prices, and inventory levels.
     - `orders`: 400 customer orders with statuses, dates, and payment methods.
     - `order_items`: ~800 item-level transaction records.
     - `product_reviews`: 150 customer reviews with 1-5 star ratings.
   - Seed with one click from the UI or import `dummy_data.sql`.

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Create a `.env` file or configure via the app sidebar:
```env
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_MODEL=sarvam-105b

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=retail_analytics_db
```

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```text
servam/
├── app.py                  # Main Streamlit web application & chat UI
├── db_connector.py         # MySQL connection, schema introspection & safety checks
├── sql_generator.py        # Sarvam AI API integration & prompt engineering
├── visualizer.py           # Intelligent Plotly chart generator
├── generate_dummy_data.py  # Dummy e-commerce data generator & seeder
├── dummy_data.sql          # Pre-generated SQL schema and data dump
├── config.py               # Settings and environment variable loader
├── requirements.txt        # Python package dependencies
└── README.md               # Documentation
```
