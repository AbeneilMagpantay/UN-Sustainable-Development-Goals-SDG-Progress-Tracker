<div align="center">

# UN Sustainable Development Goals Progress Tracker

**An end-to-end data engineering platform tracking global progress toward the United Nations' 17 Sustainable Development Goals across 190+ countries.**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-1.11-orange?logo=dbt)](https://getdbt.com)
[![BigQuery](https://img.shields.io/badge/Google-BigQuery-4285F4?logo=google-cloud)](https://cloud.google.com/bigquery)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=power-bi)](https://powerbi.microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[View Dashboard](#dashboard) • [Architecture](#architecture) • [Data Model](#data-model) • [Quick Start](#quick-start)

</div>

---

## Overview

This project demonstrates a complete **Modern Data Stack** implementation, extracting data from official UN and World Bank APIs, transforming it using industry-standard tools, and visualizing global SDG progress through interactive dashboards.

### Key Features

- **17 SDGs tracked** across **190+ countries** with **25 years of historical data** (2000-2024)
- **Star schema data model** with dimension and fact tables for efficient analytics
- **Automated ETL pipeline** with data quality checks
- **Interactive Power BI dashboards** with geographic heatmaps and regional analysis
- **Year-over-year change metrics** to track improvement trends

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
│  ┌─────────────────┐                    ┌─────────────────┐                 │
│  │   UN SDG API    │                    │ World Bank API  │                 │
│  │  (unstats.un)   │                    │ (api.worldbank) │                 │
│  └────────┬────────┘                    └────────┬────────┘                 │
│           │                                      │                           │
│           └──────────────────┬───────────────────┘                           │
│                              ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    PYTHON ETL (extract_data.py)                       │  │
│  │              requests • pandas • google-cloud-bigquery                │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    GOOGLE BIGQUERY (Data Warehouse)                   │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │  │
│  │  │  RAW Layer  │───▶│   STAGING   │───▶│    MARTS    │               │  │
│  │  │  (7 tables) │    │  (4 views)  │    │ (5 tables)  │               │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘               │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                       │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │                         dbt Core (Transformations)                    │  │
│  │               SQL models • Star Schema • Data Quality Tests           │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    POWER BI (Visualization)                           │  │
│  │          Geographic Heatmaps • KPIs • Regional Analysis               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Sources** | UN SDG API, World Bank API | Official government data sources |
| **Extraction** | Python, Requests, Pandas | REST API data extraction |
| **Storage** | Google BigQuery | Serverless cloud data warehouse |
| **Transformation** | dbt Core | SQL-based data modeling & testing |
| **Visualization** | Power BI | Interactive dashboards |
| **Version Control** | Git, GitHub | Source code management |

---

## Data Model

### Star Schema Design

```
                    ┌─────────────────┐
                    │   dim_goals     │
                    │─────────────────│
                    │ goal_code (PK)  │
                    │ goal_title      │
                    │ goal_category   │
                    └────────┬────────┘
                             │
┌─────────────────┐          │          ┌─────────────────┐
│  dim_countries  │          │          │    dim_time     │
│─────────────────│          │          │─────────────────│
│ country_code(PK)│          │          │ year (PK)       │
│ country_name    │          │          │ decade          │
│ region          │────┐     │     ┌────│ development_era │
│ income_level    │    │     │     │    └─────────────────┘
└─────────────────┘    │     │     │
                       ▼     ▼     ▼
                ┌─────────────────────────┐
                │   fact_sdg_progress     │
                │─────────────────────────│
                │ progress_id (PK)        │
                │ country_code (FK)       │
                │ goal_code (FK)          │
                │ year (FK)               │
                │ avg_indicator_value     │
                │ yoy_change              │
                │ indicators_measured     │
                └─────────────────────────┘
```

### Tables

| Layer | Table | Rows | Description |
|-------|-------|------|-------------|
| Raw | `sdg_goals` | 17 | UN Sustainable Development Goals |
| Raw | `sdg_indicator_data` | 100k+ | Indicator measurements |
| Raw | `wb_countries` | 296 | World Bank country metadata |
| Mart | `dim_countries` | 460 | Country dimension with region/income |
| Mart | `dim_goals` | 17 | Goal dimension with categories |
| Mart | `dim_time` | 25 | Time dimension (2000-2024) |
| Mart | `fact_sdg_progress` | 6,800 | SDG progress fact table |
| Mart | `fact_economic_indicators` | 6,600 | Economic indicators fact table |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud account with BigQuery enabled
- Power BI Desktop (optional, for visualization)

### 1. Clone & Setup

```bash
git clone https://github.com/AbeneilMagpantay/UN-Sustainable-Development-Goals-SDG-Progress-Tracker.git
cd UN-Sustainable-Development-Goals-SDG-Progress-Tracker

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Google Cloud

1. Create a GCP project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable the BigQuery API
3. Create a service account with "BigQuery Admin" role
4. Download the JSON key file
5. Copy `.env.example` to `.env` and configure:

```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/your-key.json
GCP_PROJECT_ID=your-project-id
```

### 3. Run Data Extraction

```bash
# Test API connections first
python scripts/test_apis.py

# Extract and load data to BigQuery
python scripts/extract_data.py
```

### 4. Run dbt Transformations

```bash
cd dbt_sdg

# Test connection
dbt debug --profiles-dir .

# Build all models
dbt build --profiles-dir .
```

### 5. Data Quality Check

```bash
python scripts/data_quality_check.py
```

---

## Project Structure

```
UN-Sustainable-Development-Goals-SDG-Progress-Tracker/
├── scripts/
│   ├── test_apis.py              # API connectivity tests
│   ├── extract_data.py           # ETL pipeline
│   ├── export_for_tableau.py     # CSV export for visualization
│   └── data_quality_check.py     # Data validation
├── dbt_sdg/
│   ├── models/
│   │   ├── staging/              # Cleaned source data
│   │   │   ├── stg_sdg_goals.sql
│   │   │   ├── stg_sdg_indicator_data.sql
│   │   │   ├── stg_wb_countries.sql
│   │   │   └── stg_wb_indicators.sql
│   │   └── marts/                # Star schema tables
│   │       ├── dim_countries.sql
│   │       ├── dim_goals.sql
│   │       ├── dim_time.sql
│   │       ├── fact_sdg_progress.sql
│   │       └── fact_economic_indicators.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── data/
│   └── exports/                  # CSV exports for visualization
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Data Sources

| Source | Description | API Endpoint | Data Points |
|--------|-------------|--------------|-------------|
| UN SDG API | Official SDG indicators | `unstats.un.org/sdgapi` | 17 goals, 169 targets, 251 indicators |
| World Bank API | Economic indicators | `api.worldbank.org` | GDP, Population, Life expectancy, Literacy |

---

## Data Quality

The pipeline includes automated data quality checks:

- Null validation on key columns
- Row count verification for all tables
- Coverage analysis by region and goal
- Sample data inspection

Run quality checks with:
```bash
python scripts/data_quality_check.py
```

---

## Dashboard

Power BI dashboard with interactive visualizations:

- **World Map**: SDG progress by country (color-coded heatmap)
- **Trend Analysis**: Year-over-year progress tracking
- **Regional Comparison**: Performance by region and income level
- **Goal Breakdown**: Individual SDG performance metrics

---

## Machine Learning

The project includes an ML pipeline to predict SDG achievement by 2030:

- **Model**: Random Forest Classifier
- **Features**: Historical progress trends, YoY change, economic indicators
- **Output**: Probability score and category (On Track, Moderate Progress, At Risk, Off Track)

Run the predictor:
```bash
python ml/train_sdg_predictor.py
```

Predictions are exported to:
- BigQuery: `staging_marts.ml_sdg_predictions`
- CSV: `data/exports/ml_sdg_predictions.csv`

---

## Future Enhancements

- [ ] Implement Apache Airflow for scheduled pipeline runs
- [ ] Add dbt tests for referential integrity
- [ ] Generate dbt documentation site
- [ ] Deploy Power BI dashboard to Power BI Service

---

## Author

**Abeneil Magpantay**  
Data Engineer | AI Engineer

- GitHub: [@AbeneilMagpantay](https://github.com/AbeneilMagpantay)
- LinkedIn: [Abeneil Magpantay](https://linkedin.com/in/abeneilmagpantay)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
