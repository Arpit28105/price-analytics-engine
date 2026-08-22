# 📊 Product Price History & Sales Analytics Engine

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Containers-blue)
![Metabase](https://img.shields.io/badge/Metabase-BI-yellow)

> **An automated ETL pipeline that tracks product price changes, correlates them with sales volume, and automatically flags products where a price hike caused a significant drop in orders.**

---

## 📖 Table of Contents
- [The Problem](#-the-problem)
- [System Architecture](#-system-architecture)
- [Key Data Engineering Principles](#-key-data-engineering-principles)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
  - [Running the Pipeline](#running-the-pipeline)
- [Metabase Dashboard](#-metabase-dashboard)
- [Sample Output](#-sample-output)
- [Future Improvements](#-future-improvements)

---

## 🎯 The Problem

E-commerce platforms frequently change product prices to boost sales. However, increasing a price often drives customers away. 

**This project solves that by:**
1. **Tracking** every single price change for products using an SCD Type 2 (Slowly Changing Dimension).
2. **Correlating** those changes with daily sales volume using advanced SQL Window Functions.
3. **Automatically flagging** products where a price hike caused a significant drop in orders (Negative Price Elasticity).

---

## 🏗️ System Architecture
[Data Generator (Faker)]
↓
[Data Quality Gate (validate.py)] ← If Nulls/Errors → Pipeline FAILS ❌
↓
[PostgreSQL - Staging Area]
↓ (UPSERT Logic)
[SCD Type 2 Table (dim_product)] → Tracks price history with valid_from/valid_to
↓
[Fact Table (fact_sales)] → Joins daily orders with product keys
↓
[Analytical SQL (Window Functions)] → Calculates "Price Elasticity" & Sales Velocity
↓
[Metabase Dashboard] → Visualizes price changes vs. sales drops

text

---

## ⚡ Key Data Engineering Principles

- **SCD Type 2 (Slowly Changing Dimension):** Preserves full historical price records using `valid_from`/`valid_to` timestamps. When a price changes, the old record is closed (`is_active = FALSE`) and a new one is inserted. This enables precise "what-if" analysis on pricing strategies.

- **Data Quality as a Gatekeeper:** A strict validation layer (`validate.py`) checks for nulls, negative values, and future dates. If data quality dips below 100% (or 95%), the pipeline fails gracefully rather than corrupting the data warehouse.

- **Pushdown Computation with SQL:** Instead of processing data in Python, all heavy analytical logic (rolling averages, percentage deltas) is pushed directly to the PostgreSQL engine using **Window Functions** (`LAG`, `AVG OVER ROWS`).

- **Containerization & Orchestration:** Entire stack (PostgreSQL + Metabase) runs inside Docker containers. The pipeline is scheduled daily using `APScheduler`.

---

## 🛠️ Tech Stack

| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.12 |
| **Libraries** | Pandas, Faker, Psycopg2, Python-dotenv, APScheduler |
| **Database** | PostgreSQL 15 (Running via Docker on port 5433) |
| **BI Tool** | Metabase (Running via Docker on port 3000) |
| **Containerization** | Docker & Docker Compose |
| **Version Control** | Git & GitHub |

---

## 📁 Project Structure
price-analytics-engine/
├── docker-compose.yml # Postgres (5433) + Metabase (3000)
├── requirements.txt # Python dependencies
├── .env # Database credentials (gitignored)
├── .env.example # Template for credentials
├── README.md # This documentation
├── src/
│ ├── generate_data.py # Synthetic data generation (Faker)
│ ├── validate.py # Data Quality Gatekeeper
│ ├── load_to_db.py # SCD Type 2 UPSERT logic
│ ├── run_analytics.py # Executes the SQL views
│ ├── analytics.sql # Window Functions (LAG, Rolling Averages)
│ └── pipeline.py # APScheduler orchestrator
├── data/ # Generated CSV files (gitignored)
└── logs/ # Pipeline run logs (gitignored)

text

---

## 🚀 Getting Started

### Prerequisites

- **Docker Desktop** (with WSL2 enabled for Windows)
- **Python 3.9+** installed
- **Git** installed

### Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/yourusername/price-analytics-engine.git
cd price-analytics-engine
2. Create a virtual environment and install dependencies

bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
3. Configure Environment Variables

Create a .env file in the root directory:

env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=price_analytics
DB_USER=postgres
DB_PASSWORD=postgres
(Note: Port is set to 5433 to avoid conflicts with any existing local PostgreSQL installations on your machine).

4. Spin up the Docker Containers

bash
docker compose up -d
Verify the containers are running:

bash
docker ps
You should see both postgres_db and metabase_bi listed.

Running the Pipeline
Test Run (Immediate Execution)

To run the entire pipeline once to verify everything works:

bash
python src/pipeline.py --now
Scheduled Runs (Daily Automation)

The pipeline is automatically scheduled to run every day at 9:00 AM. To keep it running in the background:

bash
python src/pipeline.py
(Press CTRL+C to stop the scheduler).

📈 Metabase Dashboard
Once the pipeline has run successfully, open Metabase:

text
http://localhost:3000
Initial Setup:

Create your admin account.

Connect to the database with these credentials:

Host: postgres (if using Docker network) or localhost

Port: 5433

Database: price_analytics

User: postgres

Password: postgres

Dashboard Cards Included:

Card	Type	Description
Pipeline Health Monitor	Table	Shows the latest pipeline run status (SUCCESS/FAILED).
High-Risk Elasticity Alerts	Table	Flags products where a price hike > 10% caused a sales drop.
Daily Aggregate Sales Volume	Line Chart	Visualizes total daily sales over the last 90 days.
🔍 Sample Output
Analytical Alert Example (from analytics.sql):

text
Product: P001 (Darkolivegreen Ago) | Price Δ: +10.68% | Sales Δ: -6.19% | Status: HIGH RISK (ELASTIC DROP)
Product: P003 (Ivory Chair)       | Price Δ: +24.91% | Sales Δ: -21.62% | Status: HIGH RISK (ELASTIC DROP)
SQL Logic Used:

LAG(price) to calculate the percentage change in price.

AVG(quantity_sold) OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) to compute a 7-day rolling sales average.

💡 Future Improvements
Idempotent UPSERTS: Add INSERT ... ON CONFLICT to the loader to prevent duplicate runs from breaking historical records.

Unit Testing: Implement pytest for the validation and loader modules.

Airflow Integration: Replace APScheduler with Apache Airflow for production-grade monitoring and retries.

Real-Time Data: Swap out the Faker generator for a real API (e.g., Shopify or Stripe webhooks).

🤝 Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🏆 Acknowledgments
Built as a portfolio project to demonstrate proficiency in Data Engineering, ETL pipelines, Dimensional Modeling (SCD Type 2), and Business Intelligence.